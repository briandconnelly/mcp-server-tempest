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
        value=first.get("input"),
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
            raise wfe.to_tool_error(rid) from exc

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
