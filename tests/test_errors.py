"""Tests for the structured-error model."""

import pytest

from mcp_server_tempest.errors import _TEMPORARY, ErrorCode, WeatherFlowError


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


class TestWeatherFlowErrorPayload:
    def test_minimal_payload(self):
        wfe = WeatherFlowError(
            code=ErrorCode.AUTH_INVALID,
            message="bad token",
        )
        payload = wfe.to_payload(request_id="abc123")
        assert payload == {
            "code": "auth_invalid",
            "message": "bad token",
            "temporary": False,
            "request_id": "abc123",
        }

    def test_temporary_true_for_rate_limited(self):
        wfe = WeatherFlowError(code=ErrorCode.RATE_LIMITED, message="slow down")
        assert wfe.temporary is True
        assert wfe.to_payload("rid")["temporary"] is True

    def test_temporary_true_for_upstream_unavailable(self):
        wfe = WeatherFlowError(code=ErrorCode.UPSTREAM_UNAVAILABLE, message="down")
        assert wfe.temporary is True

    def test_temporary_false_for_others(self):
        for code in ErrorCode:
            if code in _TEMPORARY:
                continue
            assert WeatherFlowError(code=code, message="x").temporary is False

    def test_optional_fields_included_when_set(self):
        wfe = WeatherFlowError(
            code=ErrorCode.STATION_NOT_FOUND,
            message="no such station",
            hint="call get_stations",
            field_name="station_id",
            value=99999,
            next={"tool": "get_stations"},
            details={"upstream_status": 404, "operation": "observation"},
        )
        payload = wfe.to_payload("rid")
        assert payload["hint"] == "call get_stations"
        assert payload["field"] == "station_id"  # JSON key is "field", attr is field_name
        assert payload["value"] == 99999
        assert payload["next"] == {"tool": "get_stations"}
        assert payload["details"] == {"upstream_status": 404, "operation": "observation"}

    def test_optional_fields_omitted_when_none(self):
        wfe = WeatherFlowError(code=ErrorCode.AUTH_INVALID, message="bad")
        payload = wfe.to_payload("rid")
        for k in ("hint", "field", "value", "next", "retry_after_ms", "details"):
            assert k not in payload, f"expected {k!r} omitted"

    def test_retry_after_ms_round_trips(self):
        wfe = WeatherFlowError(
            code=ErrorCode.RATE_LIMITED,
            message="slow",
            retry_after_ms=5000,
        )
        assert wfe.to_payload("rid")["retry_after_ms"] == 5000

    def test_value_zero_is_included(self):
        # 0 is a meaningful station_id-shaped value; must not be dropped
        wfe = WeatherFlowError(
            code=ErrorCode.STATION_NOT_FOUND,
            message="zero",
            field_name="station_id",
            value=0,
        )
        assert wfe.to_payload("rid")["value"] == 0

    def test_is_an_exception(self):
        # Must be raisable and catchable as an Exception
        with pytest.raises(WeatherFlowError):
            raise WeatherFlowError(code=ErrorCode.INTERNAL_ERROR, message="x")
