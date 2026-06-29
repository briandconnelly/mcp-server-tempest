"""Tests for server logic."""

import json
import os
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp.exceptions import ToolError

import mcp_server_tempest.server as server_module
from mcp_server_tempest.cache import DiskCache
from mcp_server_tempest.errors import ErrorCode, WeatherFlowError
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
    _get_station_details_data,
    _get_stations_data,
    _int_env,
    _relaxed_schema,
    cache,
    get_capabilities,
    get_forecast,
    get_observation,
    get_station_details,
    get_stations,
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


def _structured(result):
    """Return the structured dict whether the tool returned a dict or a ToolResult."""
    sc = getattr(result, "structured_content", None)
    return sc if sc is not None else result


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear caches and disable disk cache for test isolation."""
    cache.clear()
    server_module._fetch_times.clear()
    server_module.disk_cache = None
    with patch.object(server_module, "_get_disk_cache", return_value=None):
        yield
    cache.clear()
    server_module._fetch_times.clear()
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
            with pytest.raises(WeatherFlowError) as excinfo:
                _get_api_token()
            assert excinfo.value.code is ErrorCode.AUTH_MISSING
            assert "WEATHERFLOW_API_TOKEN" in excinfo.value.message
            assert "tempestwx.com/settings/tokens" in excinfo.value.hint

    def test_raises_when_empty(self):
        with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": ""}):
            with pytest.raises(WeatherFlowError) as excinfo:
                _get_api_token()
            assert excinfo.value.code is ErrorCode.AUTH_MISSING

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


# -- Tests for helper functions (_get_*_data) --


@pytest.mark.usefixtures("_set_token")
class TestGetStationsData:
    async def test_fetches_from_api(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            return_value=SAMPLE_STATION_DATA,
        ):
            result = (await _get_stations_data(mock_ctx, use_cache=False)).data
            assert result.status.status_code == 0
            assert len(result.stations) == 1
            assert result.stations[0].station_id == 12345
            mock_ctx.report_progress.assert_any_call(progress=0, total=1)
            mock_ctx.report_progress.assert_any_call(progress=1, total=1)

    async def test_returns_cached_data(self, mock_ctx):
        cache["stations"] = "cached_value"
        result = (await _get_stations_data(mock_ctx, use_cache=True)).data
        assert result == "cached_value"
        mock_ctx.info.assert_called_with("Using cached station data")

    async def test_bypass_cache(self, mock_ctx):
        cache["stations"] = "stale"
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            return_value=SAMPLE_STATION_DATA,
        ):
            result = (await _get_stations_data(mock_ctx, use_cache=False)).data
            assert result.stations[0].station_id == 12345

    async def test_handles_none_ctx(self):
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            return_value=SAMPLE_STATION_DATA,
        ):
            result = (await _get_stations_data(None, use_cache=False)).data
            assert result.stations[0].station_id == 12345


@pytest.mark.usefixtures("_set_token")
class TestGetStationDetailsData:
    async def test_fetches_from_api(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_station_id",
            return_value=SAMPLE_SINGLE_STATION_DATA,
        ):
            result = (await _get_station_details_data(12345, mock_ctx, use_cache=False)).data
            assert result.station_id == 12345
            mock_ctx.report_progress.assert_any_call(progress=1, total=1)

    async def test_returns_cached_data(self, mock_ctx):
        cache["station_id_12345"] = "cached_station"
        result = (await _get_station_details_data(12345, mock_ctx, use_cache=True)).data
        assert result == "cached_station"

    async def test_different_station_ids_cached_separately(self, mock_ctx):
        cache["station_id_111"] = "station_a"
        cache["station_id_222"] = "station_b"
        result_a = (await _get_station_details_data(111, mock_ctx, use_cache=True)).data
        result_b = (await _get_station_details_data(222, mock_ctx, use_cache=True)).data
        assert result_a == "station_a"
        assert result_b == "station_b"

    async def test_handles_none_ctx(self):
        with patch(
            "mcp_server_tempest.server.api_get_station_id",
            return_value=SAMPLE_SINGLE_STATION_DATA,
        ):
            result = (await _get_station_details_data(12345, None, use_cache=False)).data
            assert result.station_id == 12345


@pytest.mark.usefixtures("_set_token")
class TestGetForecastData:
    async def test_fetches_from_api(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = (await _get_forecast_data(12345, mock_ctx, use_cache=False)).data
            assert result.location_name == "Seattle"
            mock_ctx.report_progress.assert_any_call(progress=1, total=1)

    async def test_returns_cached_data(self, mock_ctx):
        cache["forecast_12345"] = "cached_forecast"
        result = (await _get_forecast_data(12345, mock_ctx, use_cache=True)).data
        assert result == "cached_forecast"

    async def test_handles_none_ctx(self):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = (await _get_forecast_data(12345, None, use_cache=False)).data
            assert result.location_name == "Seattle"


@pytest.mark.usefixtures("_set_token")
class TestGetObservationData:
    async def test_fetches_from_api(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = (await _get_observation_data(12345, mock_ctx, use_cache=False)).data
            assert result.station_id == 12345
            mock_ctx.report_progress.assert_any_call(progress=1, total=1)

    async def test_returns_cached_data(self, mock_ctx):
        cache["observation_12345"] = "cached_obs"
        result = (await _get_observation_data(12345, mock_ctx, use_cache=True)).data
        assert result == "cached_obs"

    async def test_handles_none_ctx(self):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = (await _get_observation_data(12345, None, use_cache=False)).data
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
            result = _structured(await get_stations(ctx=mock_ctx))
            assert len(result["stations"]) == 1

    async def test_get_stations_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_stations",
                side_effect=Exception("API down"),
            ),
            pytest.raises(ToolError) as excinfo,
        ):
            await get_stations(ctx=mock_ctx)
        payload = json.loads(excinfo.value.args[0])
        assert payload["code"] == "internal_error"
        assert payload["temporary"] is False
        assert "API down" not in payload["message"]
        assert payload["request_id"] in payload["hint"]

    async def test_notification_failure_does_not_fail_tool(self, mock_ctx):
        """A4: progress/log notifications are advisory. A send failure must not
        turn a successful fetch into an internal_error."""
        mock_ctx.report_progress.side_effect = RuntimeError("client disconnected")
        mock_ctx.info.side_effect = RuntimeError("client disconnected")
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            return_value=SAMPLE_STATION_DATA,
        ):
            result = _structured(await get_stations(ctx=mock_ctx))
            assert len(result["stations"]) == 1

    async def test_get_station_details(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_station_id",
            return_value=SAMPLE_SINGLE_STATION_DATA,
        ):
            result = _structured(await get_station_details(station_id=12345, ctx=mock_ctx))
            assert result["station_id"] == 12345

    async def test_get_station_details_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_station_id",
                side_effect=Exception("Not found"),
            ),
            pytest.raises(ToolError) as excinfo,
        ):
            await get_station_details(station_id=99999, ctx=mock_ctx)
        payload = json.loads(excinfo.value.args[0])
        assert payload["code"] == "internal_error"

    async def test_get_forecast(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = _structured(await get_forecast(station_id=12345, ctx=mock_ctx))
            assert result["location_name"] == "Seattle"

    async def test_get_forecast_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_forecast",
                side_effect=Exception("Timeout"),
            ),
            pytest.raises(ToolError) as excinfo,
        ):
            await get_forecast(station_id=12345, ctx=mock_ctx)
        payload = json.loads(excinfo.value.args[0])
        assert payload["code"] == "internal_error"

    async def test_get_observation(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = _structured(await get_observation(station_id=12345, ctx=mock_ctx))
            assert result["station_id"] == 12345

    async def test_get_observation_error(self, mock_ctx):
        with (
            patch(
                "mcp_server_tempest.server.api_get_observation",
                side_effect=Exception("Bad request"),
            ),
            pytest.raises(ToolError) as excinfo,
        ):
            await get_observation(station_id=12345, ctx=mock_ctx)
        payload = json.loads(excinfo.value.args[0])
        assert payload["code"] == "internal_error"

    async def test_forecast_notification_failure_does_not_fail_tool(self, mock_ctx):
        """A4: notification failure on the fetch path must not fail get_forecast
        (covers the post-fetch report_progress call site)."""
        mock_ctx.report_progress.side_effect = RuntimeError("client disconnected")
        mock_ctx.info.side_effect = RuntimeError("client disconnected")
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = _structured(await get_forecast(station_id=12345, ctx=mock_ctx))
            assert result["location_name"] == "Seattle"

    async def test_observation_notification_failure_does_not_fail_tool(self, mock_ctx):
        """A4: notification failure on the fetch path must not fail
        get_observation (covers the post-fetch report_progress call site)."""
        mock_ctx.report_progress.side_effect = RuntimeError("client disconnected")
        mock_ctx.info.side_effect = RuntimeError("client disconnected")
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = _structured(await get_observation(station_id=12345, ctx=mock_ctx))
            assert result["station_id"] == 12345


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
            result = _structured(await get_stations(ctx=mock_ctx))
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
            result = _structured(await get_station_details(station_id=12345, ctx=mock_ctx))
            assert "created_epoch" not in result
            assert "last_modified_epoch" not in result

    async def test_forecast_excludes_icons(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = _structured(await get_forecast(station_id=12345, detailed=True, ctx=mock_ctx))
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
            result = _structured(
                await get_observation(station_id=12345, detailed=True, ctx=mock_ctx)
            )
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
            result = _structured(await get_forecast(station_id=12345, ctx=mock_ctx))
            # Summary mode defaults when hours/days are omitted: 6 hourly, 2 daily
            assert len(result["forecast"]["hourly"]) == 6
            assert len(result["forecast"]["daily"]) == 2

    async def test_summary_drops_metadata(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = _structured(await get_forecast(station_id=12345, ctx=mock_ctx))
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
            result = _structured(
                await get_forecast(station_id=12345, hours=6, days=3, detailed=True, ctx=mock_ctx)
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
            result = _structured(await get_forecast(station_id=12345, detailed=True, ctx=mock_ctx))
            # Detailed + omitted hours/days means "everything available".
            # SAMPLE supplies 48 hourly / 10 daily.
            assert len(result["forecast"]["hourly"]) == 48
            assert len(result["forecast"]["daily"]) == 10
            # Nothing was explicitly requested, so it is not truncated and
            # requested_* are omitted.
            assert result["truncated"] is False
            assert "requested_hours" not in result
            assert "requested_days" not in result

    async def test_depth_exceeds_available(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = _structured(
                await get_forecast(station_id=12345, hours=48, days=10, detailed=True, ctx=mock_ctx)
            )
            assert len(result["forecast"]["hourly"]) == 48
            assert len(result["forecast"]["daily"]) == 10

    async def test_summary_respects_small_hours(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = _structured(await get_forecast(station_id=12345, hours=3, ctx=mock_ctx))
            # Summary mode: min(3, 6) = 3
            assert len(result["forecast"]["hourly"]) == 3

    async def test_boundary_hours_1_days_1(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = _structured(
                await get_forecast(station_id=12345, hours=1, days=1, detailed=True, ctx=mock_ctx)
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
            result = _structured(await get_forecast(station_id=12345, ctx=mock_ctx))
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
            result = _structured(await get_forecast(station_id=12345, detailed=True, ctx=mock_ctx))
            assert result["forecast"]["daily"] == []
            assert result["forecast"]["hourly"] == []

    async def test_observation_empty_obs(self, mock_ctx):
        empty_obs = {**SAMPLE_OBSERVATION_DATA, "obs": []}
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=empty_obs,
        ):
            result = _structured(await get_observation(station_id=12345, ctx=mock_ctx))
            assert result["obs"] == []

    async def test_observation_empty_obs_detailed(self, mock_ctx):
        empty_obs = {**SAMPLE_OBSERVATION_DATA, "obs": []}
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=empty_obs,
        ):
            result = _structured(
                await get_observation(station_id=12345, detailed=True, ctx=mock_ctx)
            )
            assert result["obs"] == []


# -- Tests for explicit depth overriding summary defaults --


@pytest.mark.usefixtures("_set_token")
class TestExplicitDepthHonored:
    """Explicit hours/days are honored as given in both modes; the summary
    defaults (6 hourly / 2 daily) apply only when an axis is omitted. An
    agent that wants 10 summary-density hours gets exactly that, with no
    second call through detailed=True."""

    async def test_summary_honors_explicit_hours(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = _structured(await get_forecast(station_id=12345, hours=10, ctx=mock_ctx))
            assert len(result["forecast"]["hourly"]) == 10
            assert result["truncated"] is False
            assert result["requested_hours"] == 10
            assert result["returned_hours"] == 10
            assert "truncation_hint" not in result
            # Omitted axis keeps the summary default.
            assert result["returned_days"] == 2
            # Summary density is preserved: an explicit count must not
            # flip the response to detailed mode.
            assert "latitude" not in result

    async def test_summary_honors_explicit_days(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = _structured(await get_forecast(station_id=12345, days=8, ctx=mock_ctx))
            assert len(result["forecast"]["daily"]) == 8
            assert result["truncated"] is False
            assert result["requested_days"] == 8
            assert result["returned_days"] == 8
            assert "truncation_hint" not in result
            assert result["returned_hours"] == 6


# -- Tests for forecast truncation transparency fields --


@pytest.mark.usefixtures("_set_token")
class TestForecastTruncationFields:
    """Verify that get_forecast surfaces truncation as structured payload
    fields (F2 from the agent-friendliness audit) so agents do not have to
    parse prose to detect the summary-mode caps.
    """

    async def test_summary_small_request_not_truncated(self, mock_ctx):
        """Requesting within the summary cap should report truncated=False
        and no truncation_hint."""
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = _structured(
                await get_forecast(station_id=12345, hours=3, days=2, ctx=mock_ctx)
            )
            assert result["truncated"] is False
            assert result["requested_hours"] == 3
            assert result["requested_days"] == 2
            assert result["returned_hours"] == 3
            assert result["returned_days"] == 2
            assert "truncation_hint" not in result

    async def test_detailed_never_truncated(self, mock_ctx):
        """detailed=True bypasses the summary caps. Combined with upstream
        supplying enough entries (SAMPLE has 48 hourly / 10 daily), the
        request is satisfied and truncated=False. See
        test_detailed_mode_upstream_shortfall for the shortfall case.
        """
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = _structured(
                await get_forecast(station_id=12345, hours=24, days=7, detailed=True, ctx=mock_ctx)
            )
            assert result["truncated"] is False
            assert result["requested_hours"] == 24
            assert result["requested_days"] == 7
            assert result["returned_hours"] == 24
            assert result["returned_days"] == 7
            assert "truncation_hint" not in result

    async def test_plain_summary_call_not_truncated(self, mock_ctx):
        """F2: a plain summary call (no hours/days) returns the default depth
        without being flagged truncated, and omits requested_* since the agent
        asked for no specific count.
        """
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            result = _structured(await get_forecast(station_id=12345, ctx=mock_ctx))
            assert result["returned_hours"] == 6
            assert result["returned_days"] == 2
            assert result["truncated"] is False
            assert "requested_hours" not in result
            assert "requested_days" not in result
            assert "truncation_hint" not in result

    async def test_detailed_mode_upstream_shortfall(self, mock_ctx):
        """If upstream returns fewer entries than requested, truncated=True
        and truncation_hint states the shortfall factually — there is no
        repair, because the missing entries do not exist upstream.
        """
        short_forecast = {
            **SAMPLE_FORECAST_DATA,
            "forecast": {
                "daily": [_make_daily_forecast(d) for d in range(1, 4)],  # only 3
                "hourly": [_make_hourly_forecast(h) for h in range(10)],  # only 10
            },
        }
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=short_forecast,
        ):
            result = _structured(
                await get_forecast(station_id=12345, hours=24, days=7, detailed=True, ctx=mock_ctx)
            )
            assert result["truncated"] is True
            assert result["requested_hours"] == 24
            assert result["returned_hours"] == 10
            assert result["requested_days"] == 7
            assert result["returned_days"] == 3
            hint = result["truncation_hint"]
            assert "only 10 hourly" in hint
            assert "requested_hours=24" in hint
            assert "only 3 daily" in hint
            assert "requested_days=7" in hint

    async def test_summary_mode_upstream_shortfall(self, mock_ctx):
        """The shortfall contract is mode-independent: an explicit request
        beyond what upstream supplies is truncated in summary mode too."""
        short_forecast = {
            **SAMPLE_FORECAST_DATA,
            "forecast": {
                "daily": [_make_daily_forecast(1)],  # only 1
                "hourly": [_make_hourly_forecast(h) for h in range(4)],  # only 4
            },
        }
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=short_forecast,
        ):
            result = _structured(await get_forecast(station_id=12345, hours=8, ctx=mock_ctx))
            assert result["truncated"] is True
            assert result["requested_hours"] == 8
            assert result["returned_hours"] == 4
            assert "only 4 hourly" in result["truncation_hint"]
            # The omitted days axis is not truncated and not echoed.
            assert "requested_days" not in result
            assert result["returned_days"] == 1

    async def test_factual_fields_always_present(self, mock_ctx):
        """truncated/returned_* are always present so agents get a consistent
        shape regardless of mode. requested_* appear only when the agent passed
        an explicit value (see test_requested_fields_only_when_explicit)."""
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            for kwargs in (
                {"detailed": True},
                {"detailed": False},
                {"hours": 1, "days": 1, "detailed": True},
                {"hours": 1, "days": 1, "detailed": False},
            ):
                result = _structured(await get_forecast(station_id=12345, ctx=mock_ctx, **kwargs))
                for key in ("truncated", "returned_hours", "returned_days"):
                    assert key in result, f"{key} missing for kwargs={kwargs}"

    async def test_requested_fields_only_when_explicit(self, mock_ctx):
        """requested_* echo only what the agent explicitly passed; they are
        omitted on an axis the agent did not constrain."""
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            return_value=SAMPLE_FORECAST_DATA,
        ):
            # Only hours given: requested_hours present, requested_days omitted.
            result = _structured(await get_forecast(station_id=12345, hours=3, ctx=mock_ctx))
            assert result["requested_hours"] == 3
            assert "requested_days" not in result

            # Neither given: both omitted.
            result = _structured(await get_forecast(station_id=12345, ctx=mock_ctx))
            assert "requested_hours" not in result
            assert "requested_days" not in result


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


# -- Tests for output schema additionalProperties lockdown --


def _walk_object_schemas(node):
    """Yield every dict in a JSON Schema tree that has type=='object'."""
    if isinstance(node, dict):
        if node.get("type") == "object":
            yield node
        for value in node.values():
            yield from _walk_object_schemas(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_object_schemas(item)


class TestSchemaAdditionalPropertiesLockdown:
    """Verify that every object schema published in tool output schemas
    sets additionalProperties: false (F4 from the audit). Locking the
    output schema lets clients detect drift if a response sprouts a field
    that wasn't in the contract; the runtime Pydantic models stay
    permissive so benign upstream additions still parse and are dropped
    on serialization.
    """

    def test_forecast_schema_locked_recursively(self):
        objects = list(_walk_object_schemas(_FORECAST_SCHEMA))
        assert objects, "expected at least one object schema in _FORECAST_SCHEMA"
        for obj in objects:
            assert obj.get("additionalProperties") is False, obj.get("title", obj)

    def test_observation_schema_locked_recursively(self):
        objects = list(_walk_object_schemas(_OBSERVATION_SCHEMA))
        assert objects
        for obj in objects:
            assert obj.get("additionalProperties") is False, obj.get("title", obj)

    def test_stations_schema_locked_recursively(self):
        objects = list(_walk_object_schemas(_STATIONS_SCHEMA))
        assert objects
        for obj in objects:
            assert obj.get("additionalProperties") is False, obj.get("title", obj)

    def test_station_schema_locked_recursively(self):
        objects = list(_walk_object_schemas(_STATION_SCHEMA))
        assert objects
        for obj in objects:
            assert obj.get("additionalProperties") is False, obj.get("title", obj)

    def test_runtime_models_remain_permissive(self):
        """Ingest must NOT forbid extras — upstream additions to the
        WeatherFlow API should be silently dropped, not raise."""
        from mcp_server_tempest.models import (
            ForecastResponse,
            ObservationResponse,
            StationsResponse,
            WeatherStation,
        )

        for model in (ForecastResponse, ObservationResponse, StationsResponse, WeatherStation):
            extra = model.model_config.get("extra")
            assert extra in (None, "ignore"), (
                f"{model.__name__} must keep extra='ignore' (got {extra!r}) so "
                "upstream WeatherFlow additions don't break ingest"
            )

        # Station: same for single station root
        assert "created_epoch" not in _STATION_SCHEMA.get("required", [])
        assert "station_id" in _STATION_SCHEMA["required"]

    def test_lockdown_preserves_explicit_additional_properties(self):
        """If an object schema already declares additionalProperties (e.g.
        a future model with ConfigDict(extra='allow') causes Pydantic to
        emit additionalProperties: true), the helper must not override it.
        """
        from mcp_server_tempest.server import _lock_additional_properties

        permissive = {
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "additionalProperties": True,
        }
        _lock_additional_properties(permissive)
        assert permissive["additionalProperties"] is True

        # And a missing key still gets filled in.
        bare = {"type": "object", "properties": {"x": {"type": "string"}}}
        _lock_additional_properties(bare)
        assert bare["additionalProperties"] is False


# -- Tests for observation summary/detailed --


@pytest.mark.usefixtures("_set_token")
class TestObservationSummaryDetailed:
    async def test_summary_drops_derived_fields(self, mock_ctx):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            return_value=SAMPLE_OBSERVATION_DATA,
        ):
            result = _structured(await get_observation(station_id=12345, ctx=mock_ctx))
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
            result = _structured(await get_observation(station_id=12345, ctx=mock_ctx))
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
            result = _structured(
                await get_observation(station_id=12345, detailed=True, ctx=mock_ctx)
            )
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


async def test_observation_summary_drops_null_optionals():
    import copy

    from mcp_server_tempest.server import get_observation

    sample = copy.deepcopy(SAMPLE_OBSERVATION_DATA)
    sample["obs"][0]["lightning_strike_last_epoch"] = None
    sample["obs"][0]["lightning_strike_last_distance"] = None

    with patch(
        "mcp_server_tempest.server.api_get_observation",
        new=AsyncMock(return_value=sample),
    ):
        with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "t"}):
            cache.clear()
            summary = _structured(await get_observation(station_id=12345))
            cache.clear()
            detailed = _structured(await get_observation(station_id=12345, detailed=True))

    s_obs = summary["obs"][0]
    d_obs = detailed["obs"][0]
    assert all(v is not None for v in s_obs.values())  # no nulls in summary
    assert "lightning_strike_last_epoch" not in s_obs  # the null optional was dropped
    assert "lightning_strike_last_epoch" in d_obs  # detailed keeps it (as None)
    assert set(d_obs.keys()) >= set(s_obs.keys())


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
            "tempest_get_stations",
            "tempest_get_station_details",
            "tempest_get_observation",
            "tempest_get_forecast",
            "tempest_get_capabilities",
        ):
            assert tool_name in text, f"{tool_name} missing from instructions"

    def test_instructions_has_section_taxonomy(self):
        text = mcp.instructions
        for marker in (
            "USE THIS SERVER",
            "DO NOT USE",
            "TOOL SELECTION",
            "NOTES",
            "AMBIENT STATE",
            "TYPICAL WORKFLOW",
            "SETUP",
            "SERVER SURFACE",
            "TRANSPORT",
        ):
            assert marker in text, f"{marker!r} missing from instructions"

    def test_instructions_carries_server_surface_fingerprint(self):
        # SERVER SURFACE acts as a lightweight capability fingerprint (§9 of
        # the agent-friendly-mcp checklist). Format is `name@version` so a
        # cached client can diff this string instead of re-walking discovery.
        # The regex enforces that *some* non-whitespace version follows the
        # `@`, catching a regression where the version interpolation drops
        # to an empty string without locking in a specific release.
        import re

        text = mcp.instructions
        assert "SERVER SURFACE" in text
        assert re.search(r"mcp-server-tempest@\S+", text), (
            "SERVER SURFACE fingerprint must carry a non-empty version after '@'"
        )

    def test_instructions_documents_ambient_state_and_transport(self):
        text = mcp.instructions
        # Every env var the server actually reads must appear by name.
        for env_var in (
            "WEATHERFLOW_API_TOKEN",
            "WEATHERFLOW_CACHE_TTL",
            "WEATHERFLOW_CACHE_SIZE",
            "WEATHERFLOW_DISK_CACHE_TTL",
        ):
            assert env_var in text, f"{env_var!r} missing from instructions"
        # Disk cache path wording — a refactor that moves the path surfaces here.
        assert "user_cache_dir" in text
        assert "mcp-server-tempest" in text
        # Transport must be named explicitly.
        assert "stdio" in text


# -- Tests for the public MCP tool/resource registry --


class TestMcpRegistry:
    """Regression guards on the actual MCP surface (tools + resources).

    The instructions string can drift away from what's really registered, so
    these tests assert against the live registry to catch reintroductions of
    removed surfaces (e.g. clear_cache) or accidental renames.
    """

    EXPECTED_TOOLS = {
        "tempest_get_stations",
        "tempest_get_station_details",
        "tempest_get_forecast",
        "tempest_get_observation",
        "tempest_get_capabilities",
    }

    REMOVED_TOOLS = {
        "get_station_id",
        "clear_cache",
    }

    async def test_registered_tools_match_expected(self):
        names = {t.name for t in await mcp.list_tools()}
        assert names == self.EXPECTED_TOOLS

    async def test_removed_tools_not_registered(self):
        names = {t.name for t in await mcp.list_tools()}
        leaked = self.REMOVED_TOOLS & names
        assert not leaked, f"removed tools reintroduced: {leaked}"

    async def test_capabilities_resource_registered(self):
        # The 0.4.0 release dropped the public weather://tempest/... resources.
        # The tempest://capabilities discovery resource was added in 0.7.0.
        resources = await mcp.list_resources()
        uris = {str(r.uri) for r in resources}
        assert uris == {"tempest://capabilities"}
        assert await mcp.list_resource_templates() == []


class TestToolAnnotations:
    """Every tool is read-only (readOnlyHint=true). openWorldHint reflects the
    interaction boundary: the four WeatherFlow-backed tools reach an external
    service and return externally mutable data (openWorldHint=true), while the
    static tempest_get_capabilities stays closed-world (openWorldHint=false).
    idempotentHint must be absent — per the MCP spec it is only meaningful
    when readOnlyHint is false, so declaring it is contract noise."""

    # Tools mapped to their expected openWorldHint value.
    _OPEN_WORLD = {
        "tempest_get_stations": True,
        "tempest_get_station_details": True,
        "tempest_get_observation": True,
        "tempest_get_forecast": True,
        "tempest_get_capabilities": False,
    }

    async def test_annotations_on_every_tool(self):
        tools = await mcp.list_tools()
        assert tools
        assert {tool.name for tool in tools} == set(self._OPEN_WORLD)
        for tool in tools:
            annotations = tool.annotations
            assert annotations is not None, tool.name
            assert annotations.readOnlyHint is True, tool.name
            assert annotations.openWorldHint is self._OPEN_WORLD[tool.name], tool.name
            assert annotations.idempotentHint is None, (
                f"{tool.name}: idempotentHint should be omitted (readOnlyHint "
                "tools are trivially idempotent; the spec scopes the hint to "
                "non-read-only tools)"
            )


# -- Tests for the capabilities tool --


class TestCapabilitiesTool:
    """tempest_get_capabilities mirrors the tempest://capabilities resource
    for clients that surface MCP resources poorly (F1 from the
    agent-friendliness audit)."""

    async def test_mirrors_capabilities_resource(self):
        import fastmcp

        with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "t"}):
            async with fastmcp.Client(mcp) as c:
                resource = await c.read_resource("tempest://capabilities")
                tool_result = await c.call_tool("tempest_get_capabilities", {})
        assert tool_result.structured_content == json.loads(resource[0].text)

    async def test_works_without_token(self):
        """Capability discovery must not require credentials — it is the
        cold-start surface an agent reads before setup is complete."""
        with patch.dict(os.environ, {}, clear=True):
            result = await get_capabilities()
        payload = result.structured_content
        assert payload["fingerprint"].startswith("sha256:")
        names = {t["name"] for t in payload["tools"]}
        assert "tempest_get_capabilities" in names

    async def test_meta_carries_fingerprint(self):
        from mcp_server_tempest.server import _FINGERPRINT, _META_KEY

        result = await get_capabilities()
        assert result.meta[_META_KEY]["fingerprint"] == _FINGERPRINT

    def test_docstring_documents_errors(self):
        doc = get_capabilities.__doc__ or ""
        assert "Errors:" in doc
        assert "internal_error" in doc
        # Reachable via the middleware Pydantic path: passing an unknown
        # argument to this no-arg tool maps to invalid_argument, so the
        # documented error contract must list it.
        assert "invalid_argument" in doc


# -- Tests for per-tool error code documentation --


class TestToolErrorDocstrings:
    """Each tool's docstring must list the error codes it can return so an
    agent can branch on `code` without invoking the tool to discover them.

    The canonical code set is `errors.ErrorCode`. `station_not_found` is
    only reachable from station-scoped operations (rest.py:_STATION_SCOPED),
    so `get_stations` is the only tool that excludes it.
    """

    # Sourced from the ErrorCode enum so a rename or removal in errors.py
    # surfaces as a test failure here, not as a stale string literal.
    SHARED_CODES = tuple(
        code.value for code in ErrorCode if code is not ErrorCode.STATION_NOT_FOUND
    )

    def test_get_stations_lists_codes(self):
        doc = get_stations.__doc__ or ""
        assert "Errors:" in doc
        for code in self.SHARED_CODES:
            assert code in doc, f"{code!r} missing from get_stations docstring"
        assert "station_not_found" not in doc, (
            "get_stations cannot return station_not_found — operation 'stations' "
            "is not in rest.py:_STATION_SCOPED"
        )

    def test_station_scoped_tools_list_codes(self):
        for tool, name in (
            (get_station_details, "tempest_get_station_details"),
            (get_forecast, "tempest_get_forecast"),
            (get_observation, "tempest_get_observation"),
        ):
            doc = tool.__doc__ or ""
            assert "Errors:" in doc, f"{name} missing Errors: block"
            for code in self.SHARED_CODES:
                assert code in doc, f"{code!r} missing from {name} docstring"
            assert "station_not_found" in doc, (
                f"{name} should document station_not_found (station-scoped)"
            )


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
    async def test_get_stations_unstructured_tool_error_becomes_internal_error(self, mock_ctx):
        # An unstructured ToolError raised inside the tool body must NOT
        # leak through — _dispatch wraps it as internal_error so the wire
        # contract holds for every error path.
        with (
            patch(
                "mcp_server_tempest.server.api_get_stations",
                side_effect=ToolError("plain prose error"),
            ),
            pytest.raises(ToolError) as excinfo,
        ):
            await get_stations(ctx=mock_ctx)
        payload = json.loads(excinfo.value.args[0])
        assert payload["code"] == "internal_error"
        # The original prose must NOT leak into the structured payload.
        assert "plain prose error" not in payload["message"]
        assert "plain prose error" not in payload.get("hint", "")

    async def test_get_stations_no_token_preserves_message(self, mock_ctx):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ToolError) as excinfo:
                await get_stations(ctx=mock_ctx)
            payload = json.loads(excinfo.value.args[0])
            assert payload["code"] == "auth_missing"
            assert "WEATHERFLOW_API_TOKEN" in payload["message"]


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
            result = (await _get_stations_data(mock_ctx, use_cache=True)).data
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
            result = (await _get_station_details_data(12345, mock_ctx, use_cache=True)).data
            assert result.station_id == 12345
            mock_ctx.info.assert_called_with("Using disk-cached station data for station 12345")


# -- Tests for _dispatch helper --


class TestDispatch:
    async def test_passes_through_successful_result(self):
        from mcp_server_tempest.server import _dispatch

        async def work():
            return {"ok": True}

        result = await _dispatch(work)
        assert result == {"ok": True}

    async def test_weatherflow_error_becomes_json_tool_error(self):
        from mcp_server_tempest.server import _dispatch

        async def work():
            raise WeatherFlowError(
                code=ErrorCode.AUTH_INVALID,
                message="bad token",
                hint="get a new one",
            )

        with pytest.raises(ToolError) as excinfo:
            await _dispatch(work)
        payload = json.loads(excinfo.value.args[0])
        assert payload["code"] == "auth_invalid"
        assert payload["message"] == "bad token"
        assert payload["hint"] == "get a new one"
        assert payload["temporary"] is False
        assert isinstance(payload["request_id"], str)
        assert len(payload["request_id"]) == 16  # secrets.token_hex(8)

    async def test_unexpected_exception_becomes_internal_error(self):
        from mcp_server_tempest.server import _dispatch

        async def work():
            raise ValueError("kaboom")

        with pytest.raises(ToolError) as excinfo:
            await _dispatch(work)
        payload = json.loads(excinfo.value.args[0])
        assert payload["code"] == "internal_error"
        # Original exception text MUST NOT leak into the message or hint
        assert "kaboom" not in payload["message"]
        assert "kaboom" not in payload.get("hint", "")
        # request_id appears in the hint so users can correlate logs
        assert payload["request_id"] in payload["hint"]

    async def test_structured_tool_error_passes_through(self):
        # If a helper has already produced a structured ToolError (e.g. via
        # WeatherFlowError.to_tool_error), _dispatch must NOT re-wrap it —
        # the original code/message/request_id are preserved verbatim.
        from mcp_server_tempest.server import _dispatch

        original = WeatherFlowError(
            code=ErrorCode.AUTH_INVALID,
            message="bad",
        ).to_tool_error("preserved-rid")

        async def work():
            raise original

        with pytest.raises(ToolError) as excinfo:
            await _dispatch(work)
        # Pass-through: same exception object, same JSON, same rid.
        assert excinfo.value is original
        payload = json.loads(excinfo.value.args[0])
        assert payload["code"] == "auth_invalid"
        assert payload["request_id"] == "preserved-rid"

    async def test_unstructured_tool_error_becomes_internal_error(self):
        # Plain ToolError("...") with no JSON body is unstructured and gets
        # wrapped as internal_error so the wire contract holds even when
        # a helper or future framework path forgets to use WeatherFlowError.
        from mcp_server_tempest.server import _dispatch

        async def work():
            raise ToolError("naked text")

        with pytest.raises(ToolError) as excinfo:
            await _dispatch(work)
        payload = json.loads(excinfo.value.args[0])
        assert payload["code"] == "internal_error"
        assert "naked text" not in payload["message"]
        assert "naked text" not in payload.get("hint", "")

    async def test_tool_error_with_unknown_code_becomes_internal_error(self):
        # JSON ToolError but with a code we don't recognize → still wrapped
        # (defends against forward-compat tampering or out-of-band sources).
        from mcp_server_tempest.server import _dispatch

        async def work():
            raise ToolError(json.dumps({"code": "NOT_OUR_CODE", "message": "x"}))

        with pytest.raises(ToolError) as excinfo:
            await _dispatch(work)
        payload = json.loads(excinfo.value.args[0])
        assert payload["code"] == "internal_error"

    async def test_distinct_request_ids(self):
        from mcp_server_tempest.server import _dispatch

        rids = []
        for _ in range(5):

            async def work():
                raise WeatherFlowError(code=ErrorCode.AUTH_INVALID, message="x")

            try:
                await _dispatch(work)
            except ToolError as te:
                rids.append(json.loads(te.args[0])["request_id"])
        assert len(set(rids)) == 5


# -- Tests for _meta on tool results --


async def test_observation_meta_reports_miss_and_fingerprint():
    from mcp_server_tempest.server import _FINGERPRINT, _META_KEY, get_observation

    with patch(
        "mcp_server_tempest.server.api_get_observation",
        new=AsyncMock(return_value=SAMPLE_OBSERVATION_DATA),
    ):
        with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "t"}):
            cache.clear()
            result = await get_observation(station_id=12345)

    fetch_meta = result.meta[_META_KEY]
    assert fetch_meta["cache"] == "miss"
    assert fetch_meta["fingerprint"] == _FINGERPRINT
    assert fetch_meta["ts_retrieved"].endswith(("+00:00", "Z"))
    # The old flat keys must be gone: unprefixed _meta names are reserved
    # for the MCP protocol itself.
    for flat_key in ("cache", "fingerprint", "ts_retrieved"):
        assert flat_key not in result.meta


def test_meta_key_is_reverse_dns_prefixed():
    from mcp_server_tempest.server import _META_KEY

    prefix, _, name = _META_KEY.partition("/")
    assert prefix == "net.bconnelly.tempest"
    assert name == "fetch"


async def test_observation_meta_reports_memory_hit():
    from mcp_server_tempest.server import _META_KEY, get_observation

    with patch(
        "mcp_server_tempest.server.api_get_observation",
        new=AsyncMock(return_value=SAMPLE_OBSERVATION_DATA),
    ):
        with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "t"}):
            cache.clear()
            await get_observation(station_id=12345)  # populate
            result = await get_observation(station_id=12345)  # hit

    assert result.meta[_META_KEY]["cache"] == "memory"


def test_validated_rejects_drifted_dict():
    # Drift = a dict that violates the locked output schema. _validated must
    # raise internal_error rather than ship it (the _meta path bypasses the
    # server's own output validation; _validated is the safety net).
    from mcp_server_tempest.server import _validated

    with pytest.raises(WeatherFlowError) as exc:
        _validated("observation", {"NOT_A_REAL_FIELD": 1}, {})
    assert exc.value.code == ErrorCode.INTERNAL_ERROR


async def test_observation_structured_content_conforms_to_advertised_schema():
    import fastmcp
    from jsonschema import Draft202012Validator

    from mcp_server_tempest.server import mcp

    with patch(
        "mcp_server_tempest.server.api_get_observation",
        new=AsyncMock(return_value=SAMPLE_OBSERVATION_DATA),
    ):
        with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "t"}):
            cache.clear()
            async with fastmcp.Client(mcp) as c:
                tool = next(t for t in await c.list_tools() if t.name == "tempest_get_observation")
                r = await c.call_tool("tempest_get_observation", {"station_id": 12345})
    # The emitted structured content validates against the schema the tool advertises.
    Draft202012Validator(tool.outputSchema).validate(r.structured_content)
