"""Structured-error model for mcp-server-tempest tool responses.

See docs/superpowers/specs/2026-05-03-structured-errors-design.md for the
contract that this module implements.
"""

import json
import re
import secrets
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from fastmcp.exceptions import ToolError


class ErrorCode(StrEnum):
    AUTH_MISSING = "auth_missing"
    AUTH_INVALID = "auth_invalid"
    AUTH_FORBIDDEN = "auth_forbidden"
    # client sent a malformed argument (caught at the schema boundary by the
    # contract middleware before the tool body runs)
    INVALID_ARGUMENT = "invalid_argument"
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

# Field names whose reflected value could be a secret. We match on whole
# name-parts (split on non-alphanumerics and camelCase) rather than substrings,
# so "api_token"/"apiKey"/"X-Auth-Key" match but "monkey"/"author" do not.
_SENSITIVE_TOKENS: frozenset[str] = frozenset(
    {
        "token",
        "secret",
        "password",
        "passwd",
        "pwd",
        "passphrase",
        "auth",
        "authorization",
        "bearer",
        "credential",
        "credentials",
        "key",
        "apikey",
    }
)
_REDACTED = "[redacted]"


def _is_sensitive_field(name: str | None) -> bool:
    """True if a field name looks like it could carry a secret value.

    Defense-in-depth for value reflection: the contract middleware already
    refuses to reflect untrusted string input, but any WeatherFlowError that
    sets a value on a sensitively-named field is redacted here too.
    """
    if not name:
        return False
    parts = re.split(r"[^A-Za-z0-9]+|(?<=[a-z0-9])(?=[A-Z])", name)
    return any(p.lower() in _SENSITIVE_TOKENS for p in parts if p)


def _new_request_id() -> str:
    """Per-call correlation id for log/error pairing. 16 hex chars (~64 bits)."""
    return secrets.token_hex(8)


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

    def __post_init__(self) -> None:
        # Populate Exception.args so str(self) and traceback rendering carry
        # the message — without this, dataclass.__init__ leaves args empty.
        super().__init__(self.message)

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
        # `None` as "absent" — `0`, `""`, etc. are meaningful. A value on a
        # sensitively-named field is redacted so a secret is never reflected
        # back into model context / transcripts / client logs.
        if self.value is not None:
            out["value"] = _REDACTED if _is_sensitive_field(self.field_name) else self.value
        if self.details:
            out["details"] = self.details
        return out

    def to_tool_error(self, request_id: str) -> ToolError:
        """Serialize to a fastmcp ToolError carrying compact JSON.

        FastMCP's transport sets isError: true on the wire automatically when
        a tool raises ToolError; the JSON we put here lands in
        content[0].text for every MCP client.
        """
        return ToolError(json.dumps(self.to_payload(request_id), separators=(",", ":")))
