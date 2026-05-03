"""Structured-error model for mcp-server-tempest tool responses.

See docs/superpowers/specs/2026-05-03-structured-errors-design.md for the
contract that this module implements.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    AUTH_MISSING = "auth_missing"
    AUTH_INVALID = "auth_invalid"
    AUTH_FORBIDDEN = "auth_forbidden"
    STATION_NOT_FOUND = "station_not_found"
    RATE_LIMITED = "rate_limited"
    # retryable: upstream is healthy-ish, just temporarily unreachable
    UPSTREAM_UNAVAILABLE = "upstream_unavailable"
    # non-retryable: upstream returned something we couldn't parse, or an
    # unexpected 4xx that doesn't map to one of the above
    UPSTREAM_INVALID_RESPONSE = "upstream_invalid_response"
    # boundary catch-all for unexpected escapes from rest.py / model layer
    INTERNAL_ERROR = "internal_error"


_TEMPORARY: frozenset[ErrorCode] = frozenset(
    {ErrorCode.RATE_LIMITED, ErrorCode.UPSTREAM_UNAVAILABLE}
)


@dataclass
class WeatherFlowError(Exception):
    """Internal exception type carrying a structured error payload.

    Raised by rest.py and helpers; converted to a JSON-bearing fastmcp
    ToolError by server.py's _dispatch helper.

    Note: the attribute is `field_name` (not `field`) to avoid shadowing
    `dataclasses.field` used for `details`. The serialized JSON key is
    still `"field"` — see `to_payload`.
    """

    code: ErrorCode
    message: str
    hint: str | None = None
    field_name: str | None = None
    value: Any = None
    next: dict[str, Any] | None = None
    retry_after_ms: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def temporary(self) -> bool:
        return self.code in _TEMPORARY

    def to_payload(self, request_id: str) -> dict[str, Any]:
        out: dict[str, Any] = {
            "code": self.code.value,
            "message": self.message,
            "temporary": self.temporary,
            "request_id": request_id,
        }
        if self.hint is not None:
            out["hint"] = self.hint
        if self.field_name is not None:
            out["field"] = self.field_name
        if self.next is not None:
            out["next"] = self.next
        if self.retry_after_ms is not None:
            out["retry_after_ms"] = self.retry_after_ms
        # `value` is included whenever it was set explicitly. We only treat
        # `None` as "absent" — `0`, `""`, etc. are meaningful.
        if self.value is not None:
            out["value"] = self.value
        if self.details:
            out["details"] = self.details
        return out
