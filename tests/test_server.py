"""Tests for server logic."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp.exceptions import ToolError

import mcp_server_tempest.server as server_module
from mcp_server_tempest.cache import DiskCache
from mcp_server_tempest.models import WeatherObservation
from mcp_server_tempest.server import (
    _FORECAST_SCHEMA,
    _OBSERVATION_SCHEMA,
    _OBSERVATION_SUMMARY_FIELDS,
    _STATION_SCHEMA,
    _STATIONS_SCHEMA,
    _get_api_token,
    _get_disk_cache,
    _get_forecast_data,
    _get_observation_data,
    _get_station_id_data,
    _get_stations_data,
    _int_env,
    _relaxed_schema,
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


def _make_daily_forecast(day_num: int = 1) -> dict:
    return {
        "air_temp_high": 80.0,
        "air_temp_low": 60.0,
        "day_num": day_num,
        "day_start_local": 1700000000 + (day_num - 1) * 86400,
        "month_num": 11,
        "icon": "clear-day",
        "conditions": "Clear",
        "precip_probability": 10,
        "precip_type": "rain",
        "precip_icon": "chance-rain",
        "sunrise": 1700000000,
        "sunset": 1700040000,
    }


def _make_hourly_forecast(hour: int = 0) -> dict:
    return {
        "air_temperature": 72.0,
        "local_day": 1 + hour // 24,
        "local_hour": hour % 24,
        "time": 1700000000 + hour * 3600,
        "precip": 0.0,
        "precip_probability": 5,
        "precip_type": None,
        "relative_humidity": 50,
        "sea_level_pressure": 30.1,
        "wind_avg": 5.0,
        "wind_direction": 180.0,
        "wind_direction_cardinal": "S",
        "wind_gust": 10.0,
        "conditions": "Clear",
        "icon": "clear-day",
        "feels_like": 72.0,
        "uv": 3.0,
    }


def _make_observation() -> dict:
    return {
        "timestamp": 1700000000,
        "air_temperature": 72.0,
        "barometric_pressure": 30.1,
        "station_pressure": 29.9,
        "pressure_trend": "steady",
        "sea_level_pressure": 30.1,
        "relative_humidity": 50,
        "precip": 0.0,
        "precip_accum_last_1hr": 0.0,
        "precip_accum_local_day": 0.0,
        "precip_accum_local_day_final": 0.0,
        "precip_accum_local_yesterday": 0.0,
        "precip_accum_local_yesterday_final": 0.0,
        "precip_analysis_type_yesterday": 0,
        "precip_minutes_local_day": 0,
        "precip_minutes_local_yesterday": 0,
        "precip_minutes_local_yesterday_final": 0,
        "wind_avg": 5.0,
        "wind_direction": 180,
        "wind_gust": 10.0,
        "wind_lull": 2.0,
        "solar_radiation": 500.0,
        "uv": 3.0,
        "brightness": 50000.0,
        "lightning_strike_last_epoch": None,
        "lightning_strike_last_distance": None,
        "lightning_strike_count": 0,
        "lightning_strike_count_last_1hr": 0,
        "lightning_strike_count_last_3hr": 0,
        "feels_like": 72.0,
        "heat_index": 72.0,
        "wind_chill": 72.0,
        "dew_point": 52.0,
        "wet_bulb_temperature": 60.0,
        "wet_bulb_globe_temperature": 65.0,
        "delta_t": 20.0,
        "air_density": 1.2,
    }


SAMPLE_FORECAST_DATA = {
    "forecast": {
        "daily": [_make_daily_forecast(d) for d in range(1, 11)],
        "hourly": [_make_hourly_forecast(h) for h in range(48)],
    },
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
    "obs": [_make_observation()],
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
    """Clear caches and disable disk cache for test isolation."""
    cache.clear()
    server_module.disk_cache = None
    with patch.object(server_module, "_get_disk_cache", return_value=None):
        yield
    cache.clear()
    server_module.disk_cache = None


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
    def test_returns_token_when_set(self):
        with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "test-token-123"}):
            token = _get_api_token()
            assert token == "test-token-123"

    def test_raises_when_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ToolError, match="not configured"):
                _get_api_token()

    def test_raises_when_empty(self):
        with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": ""}):
            with pytest.raises(ToolError, match="not configured"):
                _get_api_token()

    def test_custom_env_var(self):
        with patch.dict(os.environ, {"MY_TOKEN": "custom-token"}):
            token = _get_api_token(env_var="MY_TOKEN")
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

    async def test_handles_none_ctx(self):
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            return_value=SAMPLE_STATION_DATA,
        ):
            result = await _get_stations_data(None, use_cache=False)
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

    async def test_handles_none_ctx(self):
        with patch(
            "mcp_server_tempest.server.api_get_station_id",
            return_value=SAMPLE_SINGLE_STATION_DATA,
        ):
            result = await _get_station_id_data(12345, None, use_cache=False)
            assert result.station_id == 12345


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

    async def test_handles_none_ctx(self):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await _get_forecast_data(12345, None, use_cache=False)
            assert result.location_name == "Seattle"


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

    async def test_handles_none_ctx(self):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = await _get_observation_data(12345, None, use_cache=False)
            assert result.station_id == 12345


# -- Tests for FastMCP tool registration --


class TestToolSchemas:
    """Guard against FastMCP version bumps that might change how `Context | None`
    parameters are reflected. The `ctx` parameter is injected by FastMCP at call
    time and must never appear in a tool's public input schema."""

    async def test_ctx_not_exposed_in_any_tool_schema(self):
        tools = await mcp.list_tools()
        assert tools, "expected tools to be registered"
        for tool in tools:
            schema = getattr(tool, "inputSchema", None) or getattr(tool, "parameters", {})
            props = schema.get("properties", {}) if isinstance(schema, dict) else {}
            assert "ctx" not in props, (
                f"tool {tool.name!r} unexpectedly exposes `ctx` in its input schema"
            )


# -- Tests for tool functions --


@pytest.mark.usefixtures("_set_token")
class TestTools:
    async def test_get_stations(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            return_value=SAMPLE_STATION_DATA,
        ):
            result = await get_stations(ctx=mock_ctx)
            assert len(result["stations"]) == 1

    async def test_get_stations_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_stations",
                side_effect=Exception("API down"),
            ),
            pytest.raises(ToolError, match="Request failed"),
        ):
            await get_stations(ctx=mock_ctx)

    async def test_get_station_id(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_station_id",
            return_value=SAMPLE_SINGLE_STATION_DATA,
        ):
            result = await get_station_id(station_id=12345, ctx=mock_ctx)
            assert result["station_id"] == 12345

    async def test_get_station_id_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_station_id",
                side_effect=Exception("Not found"),
            ),
            pytest.raises(ToolError, match="Request failed"),
        ):
            await get_station_id(station_id=99999, ctx=mock_ctx)

    async def test_get_forecast(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast(station_id=12345, ctx=mock_ctx)
            assert result["location_name"] == "Seattle"

    async def test_get_forecast_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_forecast",
                side_effect=Exception("Timeout"),
            ),
            pytest.raises(ToolError, match="Request failed"),
        ):
            await get_forecast(station_id=12345, ctx=mock_ctx)

    async def test_get_observation(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = await get_observation(station_id=12345, ctx=mock_ctx)
            assert result["station_id"] == 12345

    async def test_get_observation_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_observation",
                side_effect=Exception("Bad request"),
            ),
            pytest.raises(ToolError, match="Request failed"),
        ):
            await get_observation(station_id=12345, ctx=mock_ctx)


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

    async def test_lifespan_prewarms_cache_from_disk(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "mcp_server_tempest.cache.user_cache_dir",
            lambda app_name: str(tmp_path),
        )
        from mcp_server_tempest.models import StationsResponse

        dc = DiskCache(token="test-token", ttl=3600)
        stations_data = StationsResponse(**SAMPLE_STATION_DATA)
        dc.set("stations", stations_data)

        with (
            patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "test-token"}),
            patch.object(server_module, "_get_disk_cache", return_value=dc),
        ):
            async with lifespan(mcp):
                assert "stations" in cache
                assert cache["stations"].stations[0].station_id == 12345

    async def test_lifespan_no_disk_cache_hit(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "mcp_server_tempest.cache.user_cache_dir",
            lambda app_name: str(tmp_path),
        )
        dc = DiskCache(token="test-token", ttl=3600)

        with (
            patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "test-token"}),
            patch.object(server_module, "_get_disk_cache", return_value=dc),
        ):
            async with lifespan(mcp):
                assert "stations" not in cache


# -- Tests for field exclusion --


@pytest.mark.usefixtures("_set_token")
class TestFieldExclusion:
    async def test_stations_excludes_low_value_fields(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            return_value=SAMPLE_STATION_DATA,
        ):
            result = await get_stations(ctx=mock_ctx)
            station = result["stations"][0]
            assert "created_epoch" not in station
            assert "last_modified_epoch" not in station
            assert "share_with_wf" not in station["station_meta"]
            assert "share_with_wu" not in station["station_meta"]
            # elevation should still be there
            assert "elevation" in station["station_meta"]

    async def test_station_id_excludes_low_value_fields(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_station_id",
            return_value=SAMPLE_SINGLE_STATION_DATA,
        ):
            result = await get_station_id(station_id=12345, ctx=mock_ctx)
            assert "created_epoch" not in result
            assert "last_modified_epoch" not in result

    async def test_forecast_excludes_icons(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast(station_id=12345, detailed=True, ctx=mock_ctx)
            assert "icon" not in result["current_conditions"]
            for daily in result["forecast"]["daily"]:
                assert "icon" not in daily
                assert "precip_icon" not in daily
            for hourly in result["forecast"]["hourly"]:
                assert "icon" not in hourly

    async def test_observation_excludes_outdoor_keys(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = await get_observation(station_id=12345, detailed=True, ctx=mock_ctx)
            assert "outdoor_keys" not in result

    def test_observation_summary_fields_match_model(self):
        """Ensure every field in _OBSERVATION_SUMMARY_FIELDS exists on WeatherObservation."""
        model_fields = set(WeatherObservation.model_fields)
        unknown = _OBSERVATION_SUMMARY_FIELDS - model_fields
        assert not unknown, (
            f"Fields in _OBSERVATION_SUMMARY_FIELDS not on WeatherObservation: {unknown}"
        )


# -- Tests for forecast depth --


@pytest.mark.usefixtures("_set_token")
class TestForecastDepth:
    async def test_default_summary_limits(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast(station_id=12345, ctx=mock_ctx)
            # Summary mode defaults: min(12, 6)=6 hourly, min(5, 2)=2 daily
            assert len(result["forecast"]["hourly"]) == 6
            assert len(result["forecast"]["daily"]) == 2

    async def test_summary_drops_metadata(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast(station_id=12345, ctx=mock_ctx)
            assert "latitude" not in result
            assert "longitude" not in result
            assert "timezone_offset_minutes" not in result
            # These should remain
            assert "location_name" in result
            assert "timezone" in result
            assert "units" in result

    async def test_detailed_custom_depth(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast(
                station_id=12345, hours=6, days=3, detailed=True, ctx=mock_ctx
            )
            assert len(result["forecast"]["hourly"]) == 6
            assert len(result["forecast"]["daily"]) == 3
            # Detailed keeps metadata
            assert "latitude" in result
            assert "longitude" in result

    async def test_detailed_default_depth(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast(station_id=12345, detailed=True, ctx=mock_ctx)
            # Detailed defaults: 12 hourly, 5 daily
            assert len(result["forecast"]["hourly"]) == 12
            assert len(result["forecast"]["daily"]) == 5

    async def test_depth_exceeds_available(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast(
                station_id=12345, hours=48, days=10, detailed=True, ctx=mock_ctx
            )
            assert len(result["forecast"]["hourly"]) == 48
            assert len(result["forecast"]["daily"]) == 10

    async def test_summary_respects_small_hours(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast(station_id=12345, hours=3, ctx=mock_ctx)
            # Summary mode: min(3, 6) = 3
            assert len(result["forecast"]["hourly"]) == 3

    async def test_boundary_hours_1_days_1(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast(
                station_id=12345, hours=1, days=1, detailed=True, ctx=mock_ctx
            )
            assert len(result["forecast"]["hourly"]) == 1
            assert len(result["forecast"]["daily"]) == 1


# -- Tests for empty data edge cases --


@pytest.mark.usefixtures("_set_token")
class TestEmptyData:
    async def test_forecast_empty_daily_and_hourly(self, mock_ctx):
        empty_forecast = {
            **SAMPLE_FORECAST_DATA,
            "forecast": {"daily": [], "hourly": []},
        }
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=empty_forecast,
        ):
            result = await get_forecast(station_id=12345, ctx=mock_ctx)
            assert result["forecast"]["daily"] == []
            assert result["forecast"]["hourly"] == []

    async def test_forecast_empty_detailed(self, mock_ctx):
        empty_forecast = {
            **SAMPLE_FORECAST_DATA,
            "forecast": {"daily": [], "hourly": []},
        }
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=empty_forecast,
        ):
            result = await get_forecast(station_id=12345, detailed=True, ctx=mock_ctx)
            assert result["forecast"]["daily"] == []
            assert result["forecast"]["hourly"] == []

    async def test_observation_empty_obs(self, mock_ctx):
        empty_obs = {**SAMPLE_OBSERVATION_DATA, "obs": []}
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=empty_obs,
        ):
            result = await get_observation(station_id=12345, ctx=mock_ctx)
            assert result["obs"] == []

    async def test_observation_empty_obs_detailed(self, mock_ctx):
        empty_obs = {**SAMPLE_OBSERVATION_DATA, "obs": []}
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=empty_obs,
        ):
            result = await get_observation(station_id=12345, detailed=True, ctx=mock_ctx)
            assert result["obs"] == []


# -- Tests for summary mode caps --


@pytest.mark.usefixtures("_set_token")
class TestSummaryModeCaps:
    async def test_summary_caps_hours_at_6(self, mock_ctx):
        """Passing hours=10 in summary mode should still cap at 6."""
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast(station_id=12345, hours=10, ctx=mock_ctx)
            assert len(result["forecast"]["hourly"]) == 6

    async def test_summary_caps_days_at_2(self, mock_ctx):
        """Passing days=8 in summary mode should still cap at 2."""
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = await get_forecast(station_id=12345, days=8, ctx=mock_ctx)
            assert len(result["forecast"]["daily"]) == 2


# -- Tests for _relaxed_schema --


class TestRelaxedSchema:
    def test_removes_specified_fields_from_required(self):
        from mcp_server_tempest.models import ForecastResponse

        schema = _relaxed_schema(
            ForecastResponse,
            {"$root": {"latitude"}, "CurrentConditions": {"icon"}},
        )
        assert "latitude" not in schema.get("required", [])
        # Other root fields should still be required
        assert "forecast" in schema["required"]
        assert "current_conditions" in schema["required"]

        cc = schema["$defs"]["CurrentConditions"]
        assert "icon" not in cc.get("required", [])
        assert "air_temperature" in cc["required"]

    def test_unmentioned_definitions_unchanged(self):
        from mcp_server_tempest.models import ForecastResponse

        original = ForecastResponse.model_json_schema(mode="serialization")
        relaxed = _relaxed_schema(ForecastResponse, {"$root": {"latitude"}})

        # HourlyForecast was not mentioned, should be identical
        assert (
            original["$defs"]["HourlyForecast"]["required"]
            == relaxed["$defs"]["HourlyForecast"]["required"]
        )

    def test_empty_optional_fields_returns_original(self):
        from mcp_server_tempest.models import ForecastResponse

        original = ForecastResponse.model_json_schema(mode="serialization")
        relaxed = _relaxed_schema(ForecastResponse, {})
        assert original["required"] == relaxed["required"]

    def test_server_schemas_have_no_extra_required_removals(self):
        """Verify server schemas only relax fields that are actually excluded."""
        # Forecast: icon fields should be optional, core fields required
        fc = _FORECAST_SCHEMA["$defs"]["CurrentConditions"]
        assert "icon" not in fc.get("required", [])
        assert "air_temperature" in fc["required"]
        assert "conditions" in fc["required"]

        # Observation: derived fields optional, core fields required
        obs = _OBSERVATION_SCHEMA["$defs"]["WeatherObservation"]
        assert "heat_index" not in obs.get("required", [])
        assert "air_temperature" in obs["required"]
        assert "feels_like" in obs["required"]

        # Stations: internal IDs optional, core fields required
        st = _STATIONS_SCHEMA["$defs"]["WeatherStation"]
        assert "created_epoch" not in st.get("required", [])
        assert "station_id" in st["required"]
        assert "name" in st["required"]

        # Station: same for single station root
        assert "created_epoch" not in _STATION_SCHEMA.get("required", [])
        assert "station_id" in _STATION_SCHEMA["required"]


# -- Tests for observation summary/detailed --


@pytest.mark.usefixtures("_set_token")
class TestObservationSummaryDetailed:
    async def test_summary_drops_derived_fields(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = await get_observation(station_id=12345, ctx=mock_ctx)
            obs = result["obs"][0]
            for field in (
                "heat_index",
                "wind_chill",
                "wet_bulb_temperature",
                "wet_bulb_globe_temperature",
                "delta_t",
                "air_density",
                "brightness",
                "barometric_pressure",
                "station_pressure",
                "precip_accum_local_day_final",
                "precip_accum_local_yesterday_final",
                "precip_analysis_type_yesterday",
                "precip_minutes_local_day",
                "precip_minutes_local_yesterday",
                "precip_minutes_local_yesterday_final",
            ):
                assert field not in obs, f"{field} should be excluded in summary mode"
            # Core fields should remain
            assert "air_temperature" in obs
            assert "wind_avg" in obs
            assert "feels_like" in obs

    async def test_summary_drops_metadata(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = await get_observation(station_id=12345, ctx=mock_ctx)
            assert "latitude" not in result
            assert "longitude" not in result
            assert "elevation" not in result
            assert "is_public" not in result
            assert "outdoor_keys" not in result
            # These should remain
            assert "station_id" in result
            assert "station_name" in result
            assert "timezone" in result

    async def test_detailed_keeps_all_fields(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = await get_observation(station_id=12345, detailed=True, ctx=mock_ctx)
            obs = result["obs"][0]
            assert "heat_index" in obs
            assert "wind_chill" in obs
            assert "delta_t" in obs
            assert "air_density" in obs
            # detailed still drops outdoor_keys
            assert "outdoor_keys" not in result
            # detailed keeps location metadata
            assert "latitude" in result
            assert "longitude" in result


# -- Tests for health check --


class TestHealthCheck:
    async def test_health_check(self):
        request = AsyncMock()
        response = await health_check(request)
        assert response.status_code == 200
        assert response.body == b'{"status":"ok"}'


# -- Tests for server instructions --


class TestServerInstructions:
    """Regression guards on the server-level instructions string."""

    def test_instructions_non_empty(self):
        assert mcp.instructions
        assert isinstance(mcp.instructions, str)
        assert len(mcp.instructions) > 200

    def test_instructions_lists_each_tool(self):
        text = mcp.instructions
        for tool_name in (
            "get_stations",
            "get_station_details",
            "get_observation",
            "get_forecast",
        ):
            assert tool_name in text, f"{tool_name} missing from instructions"

    def test_instructions_has_scope_sections(self):
        text = mcp.instructions
        for marker in ("USE THIS SERVER", "DO NOT USE", "TOOL SELECTION"):
            assert marker in text, f"{marker!r} missing from instructions"


# -- Tests for _int_env --


class TestIntEnv:
    def test_returns_default_when_unset(self):
        assert _int_env("NONEXISTENT_VAR_12345", 42) == 42

    def test_returns_parsed_value(self, monkeypatch):
        monkeypatch.setenv("TEST_INT_VAR", "200")
        assert _int_env("TEST_INT_VAR", 42) == 200

    def test_returns_default_on_invalid(self, monkeypatch):
        monkeypatch.setenv("TEST_INT_VAR", "not_a_number")
        assert _int_env("TEST_INT_VAR", 42) == 42


# -- Tests for _get_disk_cache --


class TestGetDiskCache:
    def test_returns_none_without_token(self, monkeypatch):
        monkeypatch.delenv("WEATHERFLOW_API_TOKEN", raising=False)
        server_module.disk_cache = None
        with patch.object(server_module, "_get_disk_cache", wraps=_get_disk_cache):
            result = _get_disk_cache()
        assert result is None

    def test_creates_disk_cache_with_token(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WEATHERFLOW_API_TOKEN", "test-token")
        monkeypatch.setattr(
            "mcp_server_tempest.cache.user_cache_dir",
            lambda app_name: str(tmp_path),
        )
        server_module.disk_cache = None
        result = _get_disk_cache()
        assert isinstance(result, DiskCache)

    def test_returns_existing_instance(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "mcp_server_tempest.cache.user_cache_dir",
            lambda app_name: str(tmp_path),
        )
        dc = DiskCache(token="test-token")
        server_module.disk_cache = dc
        result = _get_disk_cache()
        assert result is dc


# -- Tests for ToolError passthrough --


@pytest.mark.usefixtures("_set_token")
class TestToolErrorPassthrough:
    async def test_get_stations_preserves_tool_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_stations",
                side_effect=ToolError("specific error"),
            ),
            pytest.raises(ToolError, match="specific error"),
        ):
            await get_stations(ctx=mock_ctx)

    async def test_get_stations_no_token_preserves_message(self, mock_ctx):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ToolError, match="not configured"):
                await get_stations(ctx=mock_ctx)


# -- Tests for disk cache integration in server --


@pytest.mark.usefixtures("_set_token")
class TestDiskCacheIntegration:
    async def test_stations_falls_back_to_disk_cache(self, tmp_path, mock_ctx, monkeypatch):
        monkeypatch.setattr(
            "mcp_server_tempest.cache.user_cache_dir",
            lambda app_name: str(tmp_path),
        )
        from mcp_server_tempest.models import StationsResponse

        dc = DiskCache(token="test-token", ttl=3600)
        stations_data = StationsResponse(**SAMPLE_STATION_DATA)
        dc.set("stations", stations_data)

        with patch.object(server_module, "_get_disk_cache", return_value=dc):
            result = await _get_stations_data(mock_ctx, use_cache=True)
            assert result.stations[0].station_id == 12345
            mock_ctx.info.assert_called_with("Using disk-cached station data")

    async def test_stations_api_writes_to_disk_cache(self, tmp_path, mock_ctx, monkeypatch):
        monkeypatch.setattr(
            "mcp_server_tempest.cache.user_cache_dir",
            lambda app_name: str(tmp_path),
        )
        dc = DiskCache(token="test-token", ttl=3600)

        with (
            patch.object(server_module, "_get_disk_cache", return_value=dc),
            patch(
                "mcp_server_tempest.server.api_get_stations",
                return_value=SAMPLE_STATION_DATA,
            ),
        ):
            await _get_stations_data(mock_ctx, use_cache=False)

        from mcp_server_tempest.models import StationsResponse

        cached = dc.get("stations", StationsResponse)
        assert cached is not None
        assert cached.stations[0].station_id == 12345

    async def test_station_id_falls_back_to_disk_cache(self, tmp_path, mock_ctx, monkeypatch):
        monkeypatch.setattr(
            "mcp_server_tempest.cache.user_cache_dir",
            lambda app_name: str(tmp_path),
        )
        from mcp_server_tempest.models import StationResponse

        dc = DiskCache(token="test-token", ttl=3600)
        station_data = StationResponse(**SAMPLE_SINGLE_STATION_DATA)
        dc.set("station_id_12345", station_data)

        with patch.object(server_module, "_get_disk_cache", return_value=dc):
            result = await _get_station_id_data(12345, mock_ctx, use_cache=True)
            assert result.station_id == 12345
            mock_ctx.info.assert_called_with("Using disk-cached station data for station 12345")
