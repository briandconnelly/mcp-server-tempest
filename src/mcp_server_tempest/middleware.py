"""Framework-boundary contract enforcement for mcp-server-tempest.

FastMCP/Pydantic validate tool arguments *before* the tool body runs, so a
malformed argument (negative station_id, wrong type, unknown field) would
otherwise surface as an unstructured Pydantic string with no `code`. This
middleware reshapes those into the same structured-error contract the tool
bodies use (errors.py / server._dispatch), and stamps a JSON Schema dialect
onto every tool's input/output schema so strict clients need not infer it.
"""

import logging
import re
from collections.abc import Mapping, Sequence

from fastmcp.exceptions import ValidationError as FastMCPValidationError
from fastmcp.server.middleware import Middleware, MiddlewareContext
from pydantic import TypeAdapter, ValidationError

from .errors import (
    _REDACTED,
    ErrorCode,
    WeatherFlowError,
    _new_request_id,
    list_stations_repair,
    repair_call,
)

logger = logging.getLogger(__name__)

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

_UNKNOWN_ARGUMENT_TYPES = frozenset({"extra_forbidden", "unexpected_keyword_argument"})
_BOUND_KEYS = ("le", "ge")


def _safe_reflected_value(error_type: str | None, raw: object) -> object:
    """Return a value safe to echo back to the caller, or None to omit it.

    Unknown arguments carry no repair value (the name tells the caller what to
    remove), so their value is dropped whatever its type. Every tool input is
    numeric/bool, so a string is never legitimate and is the realistic
    secret-leak vector — dropped. Numeric/bool inputs are reflected.
    """
    if error_type in _UNKNOWN_ARGUMENT_TYPES:
        return None
    if isinstance(raw, (int, float)):
        return raw
    return None


def _error_name(err: Mapping) -> str | None:
    loc = err.get("loc") or ()
    return str(loc[-1]) if loc else None


_SCALAR_ADAPTERS: dict[str, TypeAdapter] = {
    "integer": TypeAdapter(int),
    "boolean": TypeAdapter(bool),
    "number": TypeAdapter(float),
}


def _typed_value(prop: object, value: object) -> int | float | bool | None:
    """The caller's value in the typed form the tool validated it into, or
    None when that form is unknown.

    Pydantic validates tool inputs in lax mode, so a still-valid argument may
    arrive as a string ("1", "true"). It is re-coerced through the published
    property's scalar type — the same lax coercion that accepted it — so the
    repair preserves it typed. The result is never a string: a value that
    passed int/bool/float validation is digits or a bool, never secret text.
    """
    if not isinstance(prop, Mapping):
        return None
    members = prop.get("anyOf")
    if not isinstance(members, list):
        members = [prop]
    types = {m.get("type") for m in members if isinstance(m, Mapping)} - {"null"}
    if len(types) != 1:
        return None
    adapter = _SCALAR_ADAPTERS.get(str(next(iter(types))))
    if adapter is None:
        return None
    try:
        typed = adapter.validate_python(value)
    except ValidationError:
        return None
    return typed if isinstance(typed, (int, float)) else None


def _repair_for(
    errors: Sequence[Mapping],
    tool_name: str,
    arguments: Mapping,
    schema: Mapping | None,
) -> dict | None:
    """One callable corrective call that fixes every reported error at once
    and preserves the caller's intent.

    Pydantic reports all argument errors together (verified: hours=100 with
    days=0 yields both), so the retry corrects or drops *each* offending
    argument. The rest are the caller's still-valid originals, normalised to
    their published scalar type. Returns None when no faithful repair can be
    built: the published input schema is unknown, or a required parameter
    could not be preserved (a repair certain to fail is worse than none).
    """
    names = [_error_name(e) for e in errors]
    unknown = [e.get("type") in _UNKNOWN_ARGUMENT_TYPES for e in errors]
    if any(n == "station_id" and not u for n, u in zip(names, unknown)):
        # A bad or missing station_id must be discovered, not corrected.
        return list_stations_repair()
    if schema is None:
        return None
    properties = schema.get("properties") or {}
    offending = {n for n in names if n is not None}
    args: dict = {}
    for k, v in arguments.items():
        if k in properties and k not in offending and v is not None:
            typed = _typed_value(properties[k], v)
            if typed is not None:
                args[k] = typed
    corrected = False
    dropped_invalid = False
    for err, name, is_unknown in zip(errors, names, unknown):
        if is_unknown or name is None or name not in properties:
            continue  # unknown arguments are dropped
        ctx = err.get("ctx") or {}
        bound = next((ctx[k] for k in _BOUND_KEYS if isinstance(ctx.get(k), int)), None)
        if bound is not None:
            args[name] = bound  # clamp to the nearest valid value
            corrected = True
        else:
            # an optional argument with an unusable value is omitted, so the
            # server applies its default
            dropped_invalid = True
    if any(r not in args for r in schema.get("required") or ()):
        return None
    if corrected:
        next_step = "retry_with_corrected_arguments"
    elif dropped_invalid or not any(unknown):
        next_step = "retry_without_invalid_arguments"
    else:
        next_step = "retry_without_unknown_arguments"
    return repair_call(next_step, tool_name, args)


# An unknown argument's *name* is caller-controlled, so it can carry a pasted
# secret just like a value can. Echo a name only when it is shaped like a real
# parameter name (lowercase snake_case, short segments — every published
# parameter is); anything else is reported as "[redacted]". A plausible typo
# such as `station` keeps its diagnostic value; `sk-proj-...`, a 32-char hex key,
# or a token segment longer than 12 characters (published names top out at 7)
# does not survive.
_PARAMETER_NAME = re.compile(r"[a-z][a-z0-9]{0,11}(?:_[a-z0-9]{1,12}){0,3}")


def _reportable_name(name: str) -> str:
    return name if _PARAMETER_NAME.fullmatch(name) else _REDACTED


def _validation_error_to_weatherflow(
    exc: ValidationError,
    tool_name: str | None = None,
    arguments: Mapping | None = None,
    schema: Mapping | None = None,
) -> WeatherFlowError:
    """Map Pydantic errors to one structured invalid_argument error.

    The first error supplies message/field/value; the repair covers all of
    them, and every unknown argument is named in details.
    """
    errors = exc.errors(include_url=False)
    first = errors[0]
    name = _error_name(first)
    error_type = first.get("type")
    unknown = error_type in _UNKNOWN_ARGUMENT_TYPES
    details: dict = {"validation_type": error_type}
    unknown_names = [
        _reportable_name(n)
        for n in (_error_name(e) for e in errors if e.get("type") in _UNKNOWN_ARGUMENT_TYPES)
        if n is not None
    ]
    if unknown_names:
        details["unknown_argument"] = unknown_names[0]
    if len(unknown_names) > 1:
        details["unknown_arguments"] = unknown_names
    if len(errors) > 1:
        details["error_count"] = len(errors)
    repair = None
    if tool_name is not None:
        repair = _repair_for(errors, tool_name, arguments or {}, schema)
    return WeatherFlowError(
        code=ErrorCode.INVALID_ARGUMENT,
        message=first.get("msg", "Invalid argument."),
        hint="Follow `repair` when present; see the tool's inputSchema for the allowed shape.",
        field_name=None if unknown else name,
        value=_safe_reflected_value(error_type, first.get("input")),
        repair=repair,
        details=details,
    )


async def _published_params(context: MiddlewareContext, tool_name: str | None) -> Mapping | None:
    """The failing tool's published input schema (properties + required),
    or None if unavailable."""
    if tool_name is None or context.fastmcp_context is None:
        return None
    tool = await context.fastmcp_context.fastmcp.get_tool(tool_name)
    if tool is None:
        return None
    return tool.parameters or {}


class TempestContractMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        try:
            return await call_next(context)
        except FastMCPValidationError as exc:
            # FastMCP 4 wraps argument-validation failures in its own
            # ValidationError with the Pydantic error as __cause__. Its message
            # is the raw Pydantic text, which reflects the rejected input, so
            # it must never reach the client unshaped.
            if not isinstance(exc.__cause__, ValidationError):
                raise
            return await self._invalid_argument(exc.__cause__, context)
        except ValidationError as exc:
            return await self._invalid_argument(exc, context)

    @staticmethod
    async def _invalid_argument(exc: ValidationError, context: MiddlewareContext):
        rid = _new_request_id()
        tool_name = getattr(context.message, "name", None)
        arguments = getattr(context.message, "arguments", None) or {}
        schema = await _published_params(context, tool_name)
        wfe = _validation_error_to_weatherflow(exc, tool_name, arguments, schema)
        logger.warning("rid=%s code=%s field=%s", rid, wfe.code.value, wfe.field_name)
        return wfe.to_tool_result(rid)

    async def on_list_tools(self, context: MiddlewareContext, call_next):
        tools = await call_next(context)
        for tool in tools:
            params = getattr(tool, "parameters", None)
            if isinstance(params, dict):
                params.setdefault("$schema", JSON_SCHEMA_DIALECT)
            out = getattr(tool, "output_schema", None)
            if isinstance(out, dict):
                out.setdefault("$schema", JSON_SCHEMA_DIALECT)
        return tools
