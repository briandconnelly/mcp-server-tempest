"""Tests for REST API wrapper functions."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from mcp_server_tempest.errors import ErrorCode
from mcp_server_tempest.rest import (
    _STATION_SCOPED,
    _retry_after_ms,
    _translate_response_error,
    api_get_forecast,
    api_get_observation,
    api_get_station_id,
    api_get_stations,
)


def _mock_api_context(return_value):
    """Create a mock WeatherFlowRestAPI async context manager."""
    mock_result = MagicMock()
    mock_result.to_dict.return_value = return_value

    mock_api = AsyncMock()
    mock_api.__aenter__ = AsyncMock(return_value=mock_api)
    mock_api.__aexit__ = AsyncMock(return_value=False)
    return mock_api, mock_result


class TestApiGetStations:
    async def test_returns_dict(self):
        mock_api, mock_result = _mock_api_context({"stations": []})
        mock_api.async_get_stations = AsyncMock(return_value=mock_result)

        with patch("mcp_server_tempest.rest.WeatherFlowRestAPI", return_value=mock_api):
            result = await api_get_stations("fake-token")
            assert result == {"stations": []}
            mock_api.async_get_stations.assert_called_once()


class TestApiGetStationId:
    async def test_returns_dict(self):
        mock_api, mock_result = _mock_api_context({"station_id": 123})
        mock_api.async_get_station = AsyncMock(return_value=[mock_result])

        with patch("mcp_server_tempest.rest.WeatherFlowRestAPI", return_value=mock_api):
            result = await api_get_station_id(123, "fake-token")
            assert result == {"station_id": 123}
            mock_api.async_get_station.assert_called_once_with(station_id=123)

    async def test_raises_on_empty_response(self):
        mock_api, _ = _mock_api_context({})
        mock_api.async_get_station = AsyncMock(return_value=[])

        with patch("mcp_server_tempest.rest.WeatherFlowRestAPI", return_value=mock_api):
            with pytest.raises(ValueError, match="No station found"):
                await api_get_station_id(99999, "fake-token")


class TestApiGetForecast:
    async def test_returns_dict(self):
        mock_api, mock_result = _mock_api_context({"forecast": {}})
        mock_api.async_get_forecast = AsyncMock(return_value=mock_result)

        with patch("mcp_server_tempest.rest.WeatherFlowRestAPI", return_value=mock_api):
            result = await api_get_forecast(123, "fake-token")
            assert result == {"forecast": {}}
            mock_api.async_get_forecast.assert_called_once_with(station_id=123)


class TestApiGetObservation:
    async def test_returns_dict(self):
        mock_api, mock_result = _mock_api_context({"obs": []})
        mock_api.async_get_observation = AsyncMock(return_value=mock_result)

        with patch("mcp_server_tempest.rest.WeatherFlowRestAPI", return_value=mock_api):
            result = await api_get_observation(123, "fake-token")
            assert result == {"obs": []}
            mock_api.async_get_observation.assert_called_once_with(station_id=123)


class TestRetryAfterMs:
    def test_seconds_form(self):
        assert _retry_after_ms({"Retry-After": "5"}) == 5000

    def test_float_seconds_form(self):
        assert _retry_after_ms({"Retry-After": "1.5"}) == 1500

    def test_missing_header_returns_none(self):
        assert _retry_after_ms({}) is None

    def test_none_headers_returns_none(self):
        assert _retry_after_ms(None) is None

    def test_http_date_form_returns_none(self):
        # We intentionally don't parse RFC 7231 §7.1.3 HTTP-date form;
        # documented behavior is "drop and degrade gracefully"
        assert _retry_after_ms({"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}) is None

    def test_empty_value_returns_none(self):
        assert _retry_after_ms({"Retry-After": ""}) is None

    def test_negative_value_returns_none(self):
        # RFC 9110 §10.2.3: delay-seconds is 1*DIGIT (non-negative).
        # Out-of-spec input — drop and degrade gracefully.
        assert _retry_after_ms({"Retry-After": "-5"}) is None

    def test_inf_value_returns_none(self):
        # `int(float("inf") * 1000)` would raise OverflowError; we filter first.
        assert _retry_after_ms({"Retry-After": "inf"}) is None

    def test_nan_value_returns_none(self):
        assert _retry_after_ms({"Retry-After": "nan"}) is None


def _make_response_error(status: int, headers: dict[str, str] | None = None):
    """Build an aiohttp.ClientResponseError with .status and .headers populated."""
    request_info = MagicMock(spec=aiohttp.RequestInfo)
    return aiohttp.ClientResponseError(
        request_info=request_info,
        history=(),
        status=status,
        message=f"HTTP {status}",
        headers=headers or {},
    )


class TestTranslateResponseError:
    def test_401_always_auth_invalid(self):
        e = _make_response_error(401)
        for op in ("stations", "station", "forecast", "observation"):
            wfe = _translate_response_error(e, operation=op)
            assert wfe.code is ErrorCode.AUTH_INVALID
            assert "tempestwx.com/settings/tokens" in wfe.hint
            assert wfe.details["upstream_status"] == 401
            assert wfe.details["operation"] == op
            assert wfe.next is None

    def test_403_station_scoped_recommends_get_stations(self):
        e = _make_response_error(403)
        for op in _STATION_SCOPED:
            wfe = _translate_response_error(e, operation=op)
            assert wfe.code is ErrorCode.AUTH_FORBIDDEN
            assert wfe.next == {"tool": "get_stations"}
            assert "station" in wfe.message.lower()

    def test_403_stations_op_no_next(self):
        e = _make_response_error(403)
        wfe = _translate_response_error(e, operation="stations")
        assert wfe.code is ErrorCode.AUTH_FORBIDDEN
        assert wfe.next is None
        assert "scope" in wfe.hint.lower()

    def test_404_station_scoped_is_station_not_found(self):
        e = _make_response_error(404)
        for op in _STATION_SCOPED:
            wfe = _translate_response_error(e, operation=op, station_id=12345)
            assert wfe.code is ErrorCode.STATION_NOT_FOUND
            assert wfe.field_name == "station_id"
            assert wfe.value == 12345
            assert wfe.next == {"tool": "get_stations"}

    def test_404_stations_op_is_invalid_response(self):
        # 404 on the /stations endpoint isn't "no such station" — it's an
        # unexpected upstream answer.
        e = _make_response_error(404)
        wfe = _translate_response_error(e, operation="stations")
        assert wfe.code is ErrorCode.UPSTREAM_INVALID_RESPONSE
        assert wfe.field_name is None

    def test_404_station_scoped_without_station_id_omits_value(self):
        # If a station-scoped op forgot to thread station_id, value stays absent
        e = _make_response_error(404)
        wfe = _translate_response_error(e, operation="observation")
        assert wfe.code is ErrorCode.STATION_NOT_FOUND
        assert wfe.value is None

    def test_429_rate_limited_with_retry_after(self):
        e = _make_response_error(429, headers={"Retry-After": "30"})
        wfe = _translate_response_error(e, operation="observation")
        assert wfe.code is ErrorCode.RATE_LIMITED
        assert wfe.retry_after_ms == 30_000
        assert wfe.temporary is True

    def test_429_without_retry_after_header(self):
        e = _make_response_error(429)
        wfe = _translate_response_error(e, operation="observation")
        assert wfe.code is ErrorCode.RATE_LIMITED
        assert wfe.retry_after_ms is None

    @pytest.mark.parametrize("status", [500, 502, 503, 504])
    def test_5xx_upstream_unavailable(self, status):
        e = _make_response_error(status)
        wfe = _translate_response_error(e, operation="forecast")
        assert wfe.code is ErrorCode.UPSTREAM_UNAVAILABLE
        assert wfe.temporary is True
        assert wfe.details["upstream_status"] == status

    def test_unexpected_4xx_is_invalid_response(self):
        e = _make_response_error(418)  # I'm a teapot
        wfe = _translate_response_error(e, operation="observation")
        assert wfe.code is ErrorCode.UPSTREAM_INVALID_RESPONSE
        assert wfe.details["upstream_status"] == 418


class TestStationScopedSet:
    def test_contains_expected_operations(self):
        assert _STATION_SCOPED == frozenset({"station", "forecast", "observation"})
