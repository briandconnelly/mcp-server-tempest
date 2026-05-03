"""Structured-error model for mcp-server-tempest tool responses.

See docs/superpowers/specs/2026-05-03-structured-errors-design.md for the
contract that this module implements.
"""

from enum import StrEnum


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
