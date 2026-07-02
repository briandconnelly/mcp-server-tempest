"""Framework-boundary contract enforcement for mcp-server-tempest.

FastMCP/Pydantic validate tool arguments *before* the tool body runs, so a
malformed argument (negative station_id, wrong type, unknown field) would
otherwise surface as an unstructured Pydantic string with no `code`. This
middleware reshapes those into the same structured-error contract the tool
bodies use (errors.py / server._dispatch), and stamps a JSON Schema dialect
onto every tool's input/output schema so strict clients need not infer it.
"""

import logging

from fastmcp.server.middleware import Middleware, MiddlewareContext
from pydantic import ValidationError

from .errors import ErrorCode, WeatherFlowError, _new_request_id

logger = logging.getLogger(__name__)

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"


def _safe_reflected_value(error_type: str | None, raw: object) -> object:
    """Return a value safe to echo back to the caller, or None to omit it.

    The offending input is attacker-controlled and could be a secret (e.g. an
    agent passing {"api_token": "sk-..."} as an unknown argument). We reflect a
    value only when it carries genuine repair signal and cannot be a secret:

    - unknown fields (extra_forbidden) carry no repair value — the field name
      already tells the caller what to remove — so the value is dropped;
    - every tool input is numeric/bool, so a *string* input is never a
      legitimate value and is the realistic secret-leak vector — dropped;
    - numeric/bool inputs (e.g. station_id=-5) are useful and not secrets.
    """
    if error_type == "extra_forbidden":
        return None
    # bool is a subclass of int; both, plus float, are safe to reflect.
    if isinstance(raw, (int, float)):
        return raw
    return None


def _validation_error_to_weatherflow(exc: ValidationError) -> WeatherFlowError:
    """Map the first Pydantic error to a structured invalid_argument error."""
    first = exc.errors(include_url=False)[0]
    loc = first.get("loc") or ()
    field = str(loc[-1]) if loc else None
    return WeatherFlowError(
        code=ErrorCode.INVALID_ARGUMENT,
        message=first.get("msg", "Invalid argument."),
        hint="Fix the argument and retry; see the tool's inputSchema for the allowed shape.",
        field_name=field,
        value=_safe_reflected_value(first.get("type"), first.get("input")),
        details={"validation_type": first.get("type")},
    )


class TempestContractMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        try:
            return await call_next(context)
        except ValidationError as exc:
            rid = _new_request_id()
            wfe = _validation_error_to_weatherflow(exc)
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
