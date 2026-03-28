"""Tests for server logic."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp.exceptions import ToolError

from mcp_server_tempest.server import (
    _get_api_token,
    _get_forecast_data,
    _get_observation_data,
    _get_station_id_data,
    _get_stations_data,
    cache,
    clear_cache,
    get_forecast,
    get_forecast_resource,
    get_observation,
    get_observation_resource,
    get_station_id,
    get_station_id_resource,
    get_stations,
    get_stations_resource,
    health_check,
    lifespan,
    mcp,
)

# -- Sample data fixtures for mocking API responses --

SAMPLE_STATION_DATA = {
    "stations": [
        {
            "station_id": 12345,
            "name": "Home",
            "public_name": "My Station",
            "latitude": 47.6,
            "longitude": -122.3,
            "timezone": "America/Los_Angeles",
            "timezone_offset_minutes": -420,
            "created_epoch": 1700000000,
            "last_modified_epoch": 1700000000,
            "is_local_mode": False,
            "station_meta": {
                "elevation": 50.0,
                "share_with_wf": True,
                "share_with_wu": False,
            },
            "devices": [
                {
                    "device_id": 1,
                    "device_type": "ST",
                    "serial_number": "ST-00001234",
                    "firmware_revision": "1.0",
                    "hardware_revision": "1",
                    "device_meta": {
                        "agl": 2.0,
                        "environment": "outdoor",
                        "name": "Tempest",
                    },
                }
            ],
            "station_items": [],
        }
    ],
    "status": {"status_code": 0, "status_message": "SUCCESS"},
}

SAMPLE_SINGLE_STATION_DATA = SAMPLE_STATION_DATA["stations"][0]

SAMPLE_UNITS = {
    "units_temp": "f",
    "units_wind": "mph",
    "units_pressure": "inhg",
    "units_precip": "in",
    "units_distance": "mi",
    "units_other": "imperial",
}

SAMPLE_CURRENT_CONDITIONS = {
    "air_temperature": 72.0,
    "conditions": "Clear",
    "feels_like": 72.0,
    "icon": "clear-day",
    "relative_humidity": 50,
    "sea_level_pressure": 30.1,
    "wind_avg": 5.0,
    "wind_gust": 10.0,
    "wind_direction": 180.0,
    "wind_direction_cardinal": "S",
    "uv": 3,
    "time": 1700000000,
}

SAMPLE_FORECAST_DATA = {
    "forecast": {"daily": [], "hourly": []},
    "current_conditions": SAMPLE_CURRENT_CONDITIONS,
    "location_name": "Seattle",
    "latitude": 47.6,
    "longitude": -122.3,
    "timezone": "America/Los_Angeles",
    "timezone_offset_minutes": -420,
    "units": SAMPLE_UNITS,
}

SAMPLE_OBSERVATION_DATA = {
    "outdoor_keys": ["air_temperature"],
    "obs": [],
    "station_id": 12345,
    "station_name": "Home",
    "public_name": "My Station",
    "latitude": 47.6,
    "longitude": -122.3,
    "elevation": 50.0,
    "is_public": True,
    "timezone": "America/Los_Angeles",
    "station_units": SAMPLE_UNITS,
    "status": {"status_code": 0, "status_message": "SUCCESS"},
}


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture()
def mock_ctx():
    """Create a mock Context."""
    ctx = AsyncMock()
    return ctx


@pytest.fixture()
def _set_token():
    """Set a fake API token for tests."""
    with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "test-token"}):
        yield


# -- Tests for _get_api_token --


class TestGetApiToken:
    async def test_returns_token_when_set(self):
        with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "test-token-123"}):
            token = await _get_api_token()
            assert token == "test-token-123"

    async def test_raises_when_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ToolError, match="not configured"):
                await _get_api_token()

    async def test_raises_when_empty(self):
        with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": ""}):
            with pytest.raises(ToolError, match="not configured"):
                await _get_api_token()

    async def test_custom_env_var(self):
        with patch.dict(os.environ, {"MY_TOKEN": "custom-token"}):
            token = await _get_api_token(env_var="MY_TOKEN")
            assert token == "custom-token"


# -- Tests for cache --


class TestCache:
    def test_cache_set_and_get(self):
        cache["test_key"] = "test_value"
        assert cache["test_key"] == "test_value"

    def test_cache_clear(self):
        cache["key1"] = "val1"
        cache["key2"] = "val2"
        cache.clear()
        assert len(cache) == 0


# -- Tests for clear_cache tool --


class TestClearCacheTool:
    async def test_clears_cache(self):
        cache["test"] = "data"
        assert len(cache) == 1

        result = await clear_cache()
        assert result == "Cache cleared successfully"
        assert len(cache) == 0

    async def test_with_context(self):
        ctx = AsyncMock()
        result = await clear_cache(ctx=ctx)
        assert result == "Cache cleared successfully"
        ctx.info.assert_called_once_with("Cache cleared")

    async def test_without_context(self):
        result = await clear_cache(ctx=None)
        assert result == "Cache cleared successfully"


# -- Tests for helper functions (_get_*_data) --


@pytest.mark.usefixtures("_set_token")
class TestGetStationsData:
    async def test_fetches_from_api(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            return_value=SAMPLE_STATION_DATA,
        ):
            result = await _get_stations_data(mock_ctx, use_cache=False)
            assert result.status.status_code == 0
            assert len(result.stations) == 1
            assert result.stations[0].station_id == 12345
            mock_ctx.report_progress.assert_any_call(progress=0, total=1)
            mock_ctx.report_progress.assert_any_call(progress=1, total=1)

    async def test_returns_cached_data(self, mock_ctx):
        cache["stations"] = "cached_value"
        result = await _get_stations_data(mock_ctx, use_cache=True)
        assert result == "cached_value"
        mock_ctx.info.assert_called_with("Using cached station data")

    async def test_bypass_cache(self, mock_ctx):
        cache["stations"] = "stale"
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            return_value=SAMPLE_STATION_DATA,
        ):
            result = await _get_stations_data(mock_ctx, use_cache=False)
            assert result.stations[0].station_id == 12345


@pytest.mark.usefixtures("_set_token")
class TestGetStationIdData:
    async def test_fetches_from_api(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_station_id",
            return_value=SAMPLE_SINGLE_STATION_DATA,
        ):
            result = await _get_station_id_data(12345, mock_ctx, use_cache=False)
            assert result.station_id == 12345
            mock_ctx.report_progress.assert_any_call(progress=1, total=1)

    async def test_returns_cached_data(self, mock_ctx):
        cache["station_id_12345"] = "cached_station"
        result = await _get_station_id_data(12345, mock_ctx, use_cache=True)
        assert result == "cached_station"

    async def test_different_station_ids_cached_separately(self, mock_ctx):
        cache["station_id_111"] = "station_a"
        cache["station_id_222"] = "station_b"
        result_a = await _get_station_id_data(111, mock_ctx, use_cache=True)
        result_b = await _get_station_id_data(222, mock_ctx, use_cache=True)
        assert result_a == "station_a"
        assert result_b == "station_b"


@pytest.mark.usefixtures("_set_token")
class TestGetForecastData:
    async def test_fetches_from_api(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await _get_forecast_data(12345, mock_ctx, use_cache=False)
            assert result.location_name == "Seattle"
            mock_ctx.report_progress.assert_any_call(progress=1, total=1)

    async def test_returns_cached_data(self, mock_ctx):
        cache["forecast_12345"] = "cached_forecast"
        result = await _get_forecast_data(12345, mock_ctx, use_cache=True)
        assert result == "cached_forecast"


@pytest.mark.usefixtures("_set_token")
class TestGetObservationData:
    async def test_fetches_from_api(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = await _get_observation_data(12345, mock_ctx, use_cache=False)
            assert result.station_id == 12345
            mock_ctx.report_progress.assert_any_call(progress=1, total=1)

    async def test_returns_cached_data(self, mock_ctx):
        cache["observation_12345"] = "cached_obs"
        result = await _get_observation_data(12345, mock_ctx, use_cache=True)
        assert result == "cached_obs"


# -- Tests for tool functions --


@pytest.mark.usefixtures("_set_token")
class TestTools:
    async def test_get_stations(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            return_value=SAMPLE_STATION_DATA,
        ):
            result = await get_stations(use_cache=False, ctx=mock_ctx)
            assert len(result.stations) == 1

    async def test_get_stations_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_stations",
                side_effect=Exception("API down"),
            ),
            pytest.raises(ToolError, match="Request failed"),
        ):
            await get_stations(use_cache=False, ctx=mock_ctx)

    async def test_get_station_id(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_station_id",
            return_value=SAMPLE_SINGLE_STATION_DATA,
        ):
            result = await get_station_id(station_id=12345, use_cache=False, ctx=mock_ctx)
            assert result.station_id == 12345

    async def test_get_station_id_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_station_id",
                side_effect=Exception("Not found"),
            ),
            pytest.raises(ToolError, match="Request failed"),
        ):
            await get_station_id(station_id=99999, use_cache=False, ctx=mock_ctx)

    async def test_get_forecast(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast(station_id=12345, use_cache=False, ctx=mock_ctx)
            assert result.location_name == "Seattle"

    async def test_get_forecast_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_forecast",
                side_effect=Exception("Timeout"),
            ),
            pytest.raises(ToolError, match="Request failed"),
        ):
            await get_forecast(station_id=12345, use_cache=False, ctx=mock_ctx)

    async def test_get_observation(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = await get_observation(station_id=12345, use_cache=False, ctx=mock_ctx)
            assert result.station_id == 12345

    async def test_get_observation_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_observation",
                side_effect=Exception("Bad request"),
            ),
            pytest.raises(ToolError, match="Request failed"),
        ):
            await get_observation(station_id=12345, use_cache=False, ctx=mock_ctx)


# -- Tests for resource functions --


@pytest.mark.usefixtures("_set_token")
class TestResources:
    async def test_get_stations_resource(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            return_value=SAMPLE_STATION_DATA,
        ):
            result = await get_stations_resource(ctx=mock_ctx)
            assert len(result.stations) == 1

    async def test_get_stations_resource_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_stations",
                side_effect=Exception("fail"),
            ),
            pytest.raises(ToolError),
        ):
            await get_stations_resource(ctx=mock_ctx)

    async def test_get_station_id_resource(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_station_id",
            return_value=SAMPLE_SINGLE_STATION_DATA,
        ):
            result = await get_station_id_resource(station_id=12345, ctx=mock_ctx)
            assert result.station_id == 12345

    async def test_get_station_id_resource_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_station_id",
                side_effect=Exception("fail"),
            ),
            pytest.raises(ToolError),
        ):
            await get_station_id_resource(station_id=12345, ctx=mock_ctx)

    async def test_get_forecast_resource(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast_resource(station_id=12345, ctx=mock_ctx)
            assert result.location_name == "Seattle"

    async def test_get_forecast_resource_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_forecast",
                side_effect=Exception("fail"),
            ),
            pytest.raises(ToolError),
        ):
            await get_forecast_resource(station_id=12345, ctx=mock_ctx)

    async def test_get_observation_resource(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = await get_observation_resource(station_id=12345, ctx=mock_ctx)
            assert result.station_id == 12345

    async def test_get_observation_resource_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_observation",
                side_effect=Exception("fail"),
            ),
            pytest.raises(ToolError),
        ):
            await get_observation_resource(station_id=12345, ctx=mock_ctx)


# -- Tests for lifespan --


class TestLifespan:
    async def test_lifespan_with_token(self):
        with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "test-token"}):
            async with lifespan(mcp):
                pass  # Should not raise

    async def test_lifespan_without_token(self):
        with patch.dict(os.environ, {}, clear=True):
            async with lifespan(mcp):
                pass  # Should warn but not raise


# -- Tests for health check --


class TestHealthCheck:
    async def test_health_check(self):
        request = AsyncMock()
        response = await health_check(request)
        assert response.status_code == 200
        assert response.body == b'{"status":"ok"}'
