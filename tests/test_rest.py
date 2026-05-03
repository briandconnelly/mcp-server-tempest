"""Tests for REST API wrapper functions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_server_tempest.rest import (
    _retry_after_ms,
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
