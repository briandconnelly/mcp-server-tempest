"""Tests for REST API wrapper functions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_server_tempest.rest import (
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
