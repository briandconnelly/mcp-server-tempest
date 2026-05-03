"""Tests for the structured-error model."""

from mcp_server_tempest.errors import ErrorCode


class TestErrorCode:
    def test_all_expected_codes_present(self):
        assert {c.value for c in ErrorCode} == {
            "auth_missing",
            "auth_invalid",
            "auth_forbidden",
            "station_not_found",
            "rate_limited",
            "upstream_unavailable",
            "upstream_invalid_response",
            "internal_error",
        }

    def test_codes_are_strings(self):
        # StrEnum: code.value is the string we serialize
        assert ErrorCode.AUTH_MISSING.value == "auth_missing"
        assert isinstance(ErrorCode.AUTH_MISSING.value, str)
