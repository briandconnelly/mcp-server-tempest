"""Tests for REST API wrapper functions."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from mcp_server_tempest.errors import ErrorCode, WeatherFlowError
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
            with pytest.raises(WeatherFlowError) as excinfo:
                await api_get_station_id(99999, "fake-token")
            assert excinfo.value.code is ErrorCode.STATION_NOT_FOUND


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


class TestApiGetStationsErrorMapping:
    async def test_401_maps_to_auth_invalid(self):
        async def boom(self):
            raise _make_response_error(401)

        with patch(
            "weatherflow4py.api.WeatherFlowRestAPI.async_get_stations",
            new=boom,
        ):
            with pytest.raises(WeatherFlowError) as excinfo:
                await api_get_stations("fake-token")
            assert excinfo.value.code is ErrorCode.AUTH_INVALID
            # Chained traceback: the upstream cause is preserved via `from e`.
            # If a future refactor drops `from e`, debugging server logs loses
            # the upstream context — this assertion locks that down.
            assert isinstance(excinfo.value.__cause__, aiohttp.ClientResponseError)
            assert excinfo.value.__cause__.status == 401

    async def test_clienterror_maps_to_upstream_unavailable(self):
        async def boom(self):
            raise aiohttp.ClientConnectionError("dns down")

        with patch(
            "weatherflow4py.api.WeatherFlowRestAPI.async_get_stations",
            new=boom,
        ):
            with pytest.raises(WeatherFlowError) as excinfo:
                await api_get_stations("fake-token")
            assert excinfo.value.code is ErrorCode.UPSTREAM_UNAVAILABLE

    async def test_marshmallow_validation_error_is_invalid_response(self):
        from marshmallow import ValidationError

        async def boom(self):
            raise ValidationError("bad field")

        with patch(
            "weatherflow4py.api.WeatherFlowRestAPI.async_get_stations",
            new=boom,
        ):
            with pytest.raises(WeatherFlowError) as excinfo:
                await api_get_stations("fake-token")
            assert excinfo.value.code is ErrorCode.UPSTREAM_INVALID_RESPONSE
            assert excinfo.value.details["exception_type"] == "ValidationError"

    async def test_json_decode_error_is_invalid_response(self):
        async def boom(self):
            raise json.JSONDecodeError("Expecting value", "", 0)

        with patch(
            "weatherflow4py.api.WeatherFlowRestAPI.async_get_stations",
            new=boom,
        ):
            with pytest.raises(WeatherFlowError) as excinfo:
                await api_get_stations("fake-token")
            assert excinfo.value.code is ErrorCode.UPSTREAM_INVALID_RESPONSE
            assert excinfo.value.details["exception_type"] == "JSONDecodeError"

    async def test_unrelated_exception_propagates_to_dispatch(self):
        # Not a parse failure — this is a server-side defect (e.g. KeyError
        # in our own code, or AttributeError from a refactor). The wrapper
        # MUST NOT silently re-label it as upstream_invalid_response; let
        # it propagate so _dispatch's internal_error boundary catches it.
        async def boom(self):
            raise KeyError("internal lookup failed")

        with patch(
            "weatherflow4py.api.WeatherFlowRestAPI.async_get_stations",
            new=boom,
        ):
            # Plain KeyError, NOT WeatherFlowError. Reaches _dispatch as bare.
            with pytest.raises(KeyError):
                await api_get_stations("fake-token")

    async def test_weatherflow_error_passes_through(self):
        async def boom(self):
            raise WeatherFlowError(code=ErrorCode.AUTH_MISSING, message="ours")

        with patch(
            "weatherflow4py.api.WeatherFlowRestAPI.async_get_stations",
            new=boom,
        ):
            with pytest.raises(WeatherFlowError) as excinfo:
                await api_get_stations("fake-token")
            assert excinfo.value.code is ErrorCode.AUTH_MISSING


class TestApiGetStationIdErrorMapping:
    async def test_404_includes_station_id_value(self):
        async def boom(self, station_id):
            raise _make_response_error(404)

        with patch(
            "weatherflow4py.api.WeatherFlowRestAPI.async_get_station",
            new=boom,
        ):
            with pytest.raises(WeatherFlowError) as excinfo:
                await api_get_station_id(99999, "fake-token")
            wfe = excinfo.value
            assert wfe.code is ErrorCode.STATION_NOT_FOUND
            assert wfe.field_name == "station_id"
            assert wfe.value == 99999

    async def test_empty_list_is_station_not_found(self):
        async def empty(self, station_id):
            return []

        with patch(
            "weatherflow4py.api.WeatherFlowRestAPI.async_get_station",
            new=empty,
        ):
            with pytest.raises(WeatherFlowError) as excinfo:
                await api_get_station_id(99999, "fake-token")
            wfe = excinfo.value
            assert wfe.code is ErrorCode.STATION_NOT_FOUND
            assert wfe.field_name == "station_id"
            assert wfe.value == 99999
            assert "upstream_status" not in wfe.details
            assert wfe.details.get("operation") == "station"


class TestApiGetForecastErrorMapping:
    async def test_403_recommends_get_stations(self):
        async def boom(self, station_id):
            raise _make_response_error(403)

        with patch(
            "weatherflow4py.api.WeatherFlowRestAPI.async_get_forecast",
            new=boom,
        ):
            with pytest.raises(WeatherFlowError) as excinfo:
                await api_get_forecast(12345, "fake-token")
            assert excinfo.value.code is ErrorCode.AUTH_FORBIDDEN
            assert excinfo.value.next == {"tool": "get_stations"}


class TestApiGetObservationErrorMapping:
    async def test_429_carries_retry_after(self):
        async def boom(self, station_id):
            raise _make_response_error(429, headers={"Retry-After": "10"})

        with patch(
            "weatherflow4py.api.WeatherFlowRestAPI.async_get_observation",
            new=boom,
        ):
            with pytest.raises(WeatherFlowError) as excinfo:
                await api_get_observation(12345, "fake-token")
            assert excinfo.value.code is ErrorCode.RATE_LIMITED
            assert excinfo.value.retry_after_ms == 10_000
