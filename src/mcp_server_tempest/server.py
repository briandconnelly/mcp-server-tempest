"""
WeatherFlow Tempest MCP Server

This module provides a Model Context Protocol (MCP) server for accessing
WeatherFlow Tempest weather station data. It exposes tools for retrieving
real-time weather observations, forecasts, and station metadata.

Features:
- Real-time weather observations from personal weather stations
- Weather forecasts and current conditions
- Station and device metadata
- Automatic caching with configurable TTL
- Support for multiple stations per user account

Setup:
    1. Get an API token from https://tempestwx.com/settings/tokens
    2. Set the WEATHERFLOW_API_TOKEN environment variable
    3. Run the server: mcp-server-tempest

Environment Variables:
    WEATHERFLOW_API_TOKEN: Your WeatherFlow API token (required)
    WEATHERFLOW_CACHE_TTL: In-memory cache TTL in seconds (default: 300)
    WEATHERFLOW_CACHE_SIZE: Maximum in-memory cache entries (default: 100)
    WEATHERFLOW_DISK_CACHE_TTL: Disk cache TTL in seconds (default: 86400).
        Per-token JSON files under platformdirs.user_cache_dir(
        "mcp-server-tempest"). Used by get_stations and get_station_details.

Example Usage:
    # Get available stations
    stations = await client.call_tool("get_stations")

    # Get current conditions for a specific station
    conditions = await client.call_tool("get_observation", {"station_id": 12345})

    # Get the forecast
    forecast = await client.call_tool("get_forecast", {"station_id": 12345})
"""

import json
import logging
import os
import secrets
import traceback
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated, TypeVar

from cachetools import TTLCache
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from .cache import DiskCache
from .errors import ErrorCode, WeatherFlowError
from .models import (
    ForecastResponse,
    ObservationResponse,
    StationResponse,
    StationsResponse,
)
from .rest import (
    api_get_forecast,
    api_get_observation,
    api_get_station_id,
    api_get_stations,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _new_request_id() -> str:
    """Per-call correlation id for log/error pairing. 16 hex chars (~64 bits)."""
    return secrets.token_hex(8)


_KNOWN_CODES: frozenset[str] = frozenset(c.value for c in ErrorCode)


def _is_structured_tool_error(te: ToolError) -> bool:
    """True iff the ToolError message is a JSON payload with a known code.

    `WeatherFlowError.to_tool_error` produces this exact shape; anything else
    is unstructured and must not bypass _dispatch's wire-contract enforcement.
    """
    if not te.args:
        return False
    try:
        payload = json.loads(te.args[0])
    except (TypeError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and payload.get("code") in _KNOWN_CODES


async def _dispatch(work: Callable[[], Awaitable[T]]) -> T:
    """Run a tool body. Convert WeatherFlowError → structured JSON ToolError;
    pass through ToolErrors that already carry a structured payload; convert
    everything else (including unstructured ToolErrors) → internal_error.
    Always log with rid.
    """
    rid = _new_request_id()
    try:
        return await work()
    except WeatherFlowError as wfe:
        logger.warning("rid=%s code=%s msg=%s", rid, wfe.code.value, wfe.message)
        raise wfe.to_tool_error(rid) from wfe
    except ToolError as te:
        # Pass through ONLY if already structured. Plain ToolError("text") from
        # a helper or future framework path would otherwise leak as unstructured
        # text and defeat the wire contract; wrap it as internal_error instead.
        if _is_structured_tool_error(te):
            logger.debug("rid=%s passing through pre-structured ToolError", rid)
            raise
        logger.error("rid=%s caught unstructured ToolError: %r", rid, te.args)
        wfe = WeatherFlowError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Unexpected server error.",
            hint=f"Check server logs for request_id={rid}.",
        )
        raise wfe.to_tool_error(rid) from te
    except Exception as exc:
        logger.error("rid=%s unexpected: %s\n%s", rid, exc, traceback.format_exc())
        wfe = WeatherFlowError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Unexpected server error.",
            hint=f"Check server logs for request_id={rid}.",
        )
        raise wfe.to_tool_error(rid) from exc


def _int_env(name: str, default: int) -> int:
    """Read an integer from an environment variable with a default."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("%s=%r is not a valid integer, using default %d", name, value, default)
        return default


cache = TTLCache(
    maxsize=_int_env("WEATHERFLOW_CACHE_SIZE", 100),
    ttl=_int_env("WEATHERFLOW_CACHE_TTL", 300),
)

disk_cache: DiskCache | None = None


def _get_disk_cache() -> DiskCache | None:
    """Get or lazily initialize the disk cache, scoped to the current API token."""
    global disk_cache  # noqa: PLW0603
    if disk_cache is not None:
        return disk_cache
    token = os.getenv("WEATHERFLOW_API_TOKEN")
    if token:
        disk_cache = DiskCache(token)
    return disk_cache


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Validate configuration on startup and pre-warm caches."""
    token = os.getenv("WEATHERFLOW_API_TOKEN")
    if not token:
        logger.warning(
            "WEATHERFLOW_API_TOKEN is not set. Get a token at https://tempestwx.com/settings/tokens"
        )
    else:
        logger.info("WeatherFlow Tempest server starting")
        dc = _get_disk_cache()
        if dc:
            hit = dc.get("stations", StationsResponse)
            if hit is not None:
                cache["stations"] = hit
                logger.info(
                    "Pre-warmed stations cache from disk (%d stations)",
                    len(hit.stations),
                )
    yield


# Create the MCP server
mcp = FastMCP(
    name="WeatherFlow Tempest API Server",
    instructions="""\
WeatherFlow Tempest — read-only access to a user's personal Tempest weather
station(s). Not a global weather service.

USE THIS SERVER when the user asks about:
- Current conditions on their station ("is it raining", "how warm is it",
  "wind speed", "humidity", "UV", "pressure", "any lightning nearby")
- Their local forecast ("will it rain tomorrow", "this week's outlook",
  "10-day forecast")
- Station inventory, location, devices ("what stations do I have", "where
  is my station", "elevation", "what timezone")

DO NOT USE for:
- Locations away from the user's station, or general/global weather —
  use a public weather API
- Air quality, pollen, smoke index — not provided
- Severe-weather alerts, radar imagery, watches/warnings — not provided
- Historical analysis beyond what the live API returns (no archive)

TOOL SELECTION:
- "How many / list my stations"              -> get_stations
    (returns full station listing — id, name, location, devices, capabilities)
- "Deeper config / hardware for one station" -> get_station_details(station_id)
- "Current conditions / right now"           -> get_observation(station_id)
- "Forecast / later / tomorrow / this week"  -> get_forecast(station_id)

NOTES:
- Units follow each station's config — read 'station_units' / 'units' fields.
  Never assume °F vs °C or mph vs km/h.
- get_stations already returns devices and capabilities for each station —
  only call get_station_details if you need the deeper per-station record.
- get_forecast also returns a current snapshot — but prefer get_observation
  for current-only questions (lighter response).
- get_forecast accepts hours (1-48) and days (1-10), but the default summary
  response is capped to at most 6 hourly / 2 daily entries — smaller hours/
  days values are still honored. Pass detailed=True to use the full hours/
  days ranges (and to get raw/full sensor data) — it returns a much larger
  response.

AMBIENT STATE (env vars and side state the server reads):
- WEATHERFLOW_CACHE_TTL — in-memory TTL in seconds (default 300).
- WEATHERFLOW_CACHE_SIZE — max in-memory entries (default 100).
- WEATHERFLOW_DISK_CACHE_TTL — disk cache TTL in seconds (default 86400).
- Disk cache: per-token subdirectory (hash-keyed for account isolation)
  under platformdirs user_cache_dir("mcp-server-tempest"). Survives
  restarts.
- Cache scope: WEATHERFLOW_CACHE_TTL / WEATHERFLOW_CACHE_SIZE govern an
  in-memory cache used by all four tools. Disk cache
  (WEATHERFLOW_DISK_CACHE_TTL) applies only to get_stations and
  get_station_details. To clear: ask the user to restart the server for
  the in-memory cache; delete the cache directory above for disk.

TYPICAL WORKFLOW:
1. If you don't already have a station_id, call get_stations first.
   Station ids are not guessable — don't fabricate one.
2. Then get_observation(station_id) or get_forecast(station_id).
   If get_stations returned one station, use it without asking.

SETUP (required):
- WEATHERFLOW_API_TOKEN — get one at https://tempestwx.com/settings/tokens.

TRANSPORT: stdio. The packaged entry point `mcp-server-tempest` (e.g. via
`uvx`) speaks MCP over stdio.
""",
    lifespan=lifespan,
    on_duplicate="error",
)


def _get_api_token(env_var: str = "WEATHERFLOW_API_TOKEN") -> str:
    if not (token := os.getenv(env_var)):
        raise WeatherFlowError(
            code=ErrorCode.AUTH_MISSING,
            message=f"{env_var} is not configured.",
            hint=(f"Set {env_var}. Generate a token at https://tempestwx.com/settings/tokens"),
        )
    return token


# ---------------------------------------------------------------------------
# Output schemas and field exclusion sets.
#
# Tools return filtered dicts (via model_dump(exclude=...)) to reduce LLM
# context, but we still want clients to see a typed outputSchema. We generate
# schemas from the Pydantic models and then mark only the *actually excluded*
# fields as non-required so that:
#   - Clients know exactly which fields are guaranteed vs. optional
#   - FastMCP's output validation passes for filtered responses
#   - The schema accurately describes what the tool returns
# ---------------------------------------------------------------------------


def _relaxed_schema(
    model_class: type[BaseModel],
    optional_fields: dict[str, set[str]],
) -> dict:
    """Generate a JSON schema where only specified fields are made non-required.

    Args:
        model_class: The Pydantic model to generate the schema from.
        optional_fields: Mapping of schema definition name (or "$root" for the
            top-level object) to the set of field names that should be removed
            from that definition's ``required`` list.
    """
    schema = model_class.model_json_schema(mode="serialization")

    def _relax(obj: dict, name: str) -> None:
        fields = optional_fields.get(name, set())
        if fields and "required" in obj:
            obj["required"] = [r for r in obj["required"] if r not in fields]

    # Top-level
    _relax(schema, "$root")

    # $defs
    for def_name, defn in schema.get("$defs", {}).items():
        _relax(defn, def_name)

    return schema


_STATIONS_SCHEMA = _relaxed_schema(
    StationsResponse,
    {
        "WeatherStation": {
            "created_epoch",
            "last_modified_epoch",
        },
        "StationMeta": {"share_with_wf", "share_with_wu"},
        "StationItem": {"station_item_id", "location_id", "location_item_id"},
        "StationCapability": {"device_id", "agl", "show_precip_final"},
    },
)

_STATION_SCHEMA = _relaxed_schema(
    StationResponse,
    {
        "$root": {"created_epoch", "last_modified_epoch"},
        "StationMeta": {"share_with_wf", "share_with_wu"},
        "StationItem": {"station_item_id", "location_id", "location_item_id"},
        "StationCapability": {"device_id", "agl", "show_precip_final"},
    },
)

_FORECAST_SCHEMA = _relaxed_schema(
    ForecastResponse,
    {
        "$root": {"latitude", "longitude", "timezone_offset_minutes"},
        "CurrentConditions": {"icon"},
        "DailyForecast": {"icon", "precip_icon"},
        "HourlyForecast": {"icon"},
    },
)

_OBSERVATION_SCHEMA = _relaxed_schema(
    ObservationResponse,
    {
        "$root": {"outdoor_keys", "latitude", "longitude", "elevation", "is_public"},
        "WeatherObservation": {
            "barometric_pressure",
            "station_pressure",
            "heat_index",
            "wind_chill",
            "wet_bulb_temperature",
            "wet_bulb_globe_temperature",
            "delta_t",
            "air_density",
            "brightness",
            "precip_accum_local_day_final",
            "precip_accum_local_yesterday_final",
            "precip_analysis_type_yesterday",
            "precip_minutes_local_day",
            "precip_minutes_local_yesterday",
            "precip_minutes_local_yesterday_final",
        },
    },
)

_STATIONS_EXCLUDE: dict = {
    "stations": {
        "__all__": {
            "created_epoch": True,
            "last_modified_epoch": True,
            "station_meta": {"share_with_wf", "share_with_wu"},
            "station_items": {
                "__all__": {"station_item_id", "location_id", "location_item_id"},
            },
            "capabilities": {
                "__all__": {"device_id", "agl", "show_precip_final"},
            },
        },
    },
}

_STATION_EXCLUDE: dict = {
    "created_epoch": True,
    "last_modified_epoch": True,
    "station_meta": {"share_with_wf", "share_with_wu"},
    "station_items": {
        "__all__": {"station_item_id", "location_id", "location_item_id"},
    },
    "capabilities": {
        "__all__": {"device_id", "agl", "show_precip_final"},
    },
}

_FORECAST_EXCLUDE: dict = {
    "current_conditions": {"icon"},
    "forecast": {
        "daily": {"__all__": {"icon", "precip_icon"}},
        "hourly": {"__all__": {"icon"}},
    },
}

_OBSERVATION_EXCLUDE: dict = {
    "outdoor_keys": True,
}

# Fields to drop from each observation in summary mode.
_OBSERVATION_SUMMARY_FIELDS: set[str] = {
    "barometric_pressure",
    "station_pressure",
    "heat_index",
    "wind_chill",
    "wet_bulb_temperature",
    "wet_bulb_globe_temperature",
    "delta_t",
    "air_density",
    "brightness",
    "precip_accum_local_day_final",
    "precip_accum_local_yesterday_final",
    "precip_analysis_type_yesterday",
    "precip_minutes_local_day",
    "precip_minutes_local_yesterday",
    "precip_minutes_local_yesterday_final",
}


async def _get_stations_data(ctx: Context | None, use_cache: bool = True) -> StationsResponse:
    """Shared logic for getting stations data."""
    token = _get_api_token()

    if use_cache and "stations" in cache:
        if ctx:
            await ctx.info("Using cached station data")
        return cache["stations"]

    dc = _get_disk_cache()
    if use_cache and dc:
        hit = dc.get("stations", StationsResponse)
        if hit is not None:
            if ctx:
                await ctx.info("Using disk-cached station data")
            cache["stations"] = hit
            return hit

    if ctx:
        await ctx.report_progress(progress=0, total=1)
        await ctx.info("Getting available stations via the Tempest API")
    result = await api_get_stations(token)
    cache["stations"] = StationsResponse(**result)
    if dc:
        dc.set("stations", cache["stations"])
    if ctx:
        await ctx.report_progress(progress=1, total=1)
    return cache["stations"]


async def _get_station_details_data(
    station_id: int, ctx: Context | None, use_cache: bool = True
) -> StationResponse:
    """Shared logic for getting station details data."""
    token = _get_api_token()

    cache_id = f"station_id_{station_id}"

    if use_cache and cache_id in cache:
        if ctx:
            await ctx.info(f"Using cached station data for station {station_id}")
        return cache[cache_id]

    dc = _get_disk_cache()
    if use_cache and dc:
        hit = dc.get(cache_id, StationResponse)
        if hit is not None:
            if ctx:
                await ctx.info(f"Using disk-cached station data for station {station_id}")
            cache[cache_id] = hit
            return hit

    if ctx:
        await ctx.report_progress(progress=0, total=1)
        await ctx.info(f"Getting station ID data for station {station_id} via the Tempest API")
    result = await api_get_station_id(station_id, token)
    cache[cache_id] = StationResponse(**result)
    if dc:
        dc.set(cache_id, cache[cache_id])
    if ctx:
        await ctx.report_progress(progress=1, total=1)
    return cache[cache_id]


async def _get_forecast_data(
    station_id: int, ctx: Context | None, use_cache: bool = True
) -> ForecastResponse:
    """Shared logic for getting forecast data."""
    token = _get_api_token()

    cache_id = f"forecast_{station_id}"
    if use_cache and cache_id in cache:
        if ctx:
            await ctx.info(f"Using cached forecast data for station {station_id}")
        return cache[cache_id]

    if ctx:
        await ctx.report_progress(progress=0, total=1)
        await ctx.info(f"Getting forecast for station {station_id} via the Tempest API")
    result = await api_get_forecast(station_id, token)
    cache[cache_id] = ForecastResponse(**result)
    if ctx:
        await ctx.report_progress(progress=1, total=1)
    return cache[cache_id]


async def _get_observation_data(
    station_id: int, ctx: Context | None, use_cache: bool = True
) -> ObservationResponse:
    """Shared logic for getting observation data."""
    token = _get_api_token()

    cache_id = f"observation_{station_id}"
    if use_cache and cache_id in cache:
        if ctx:
            await ctx.info(f"Using cached observation data for station {station_id}")
        return cache[cache_id]

    if ctx:
        await ctx.report_progress(progress=0, total=1)
        await ctx.info(f"Getting observations for station {station_id} via the Tempest API")
    result = await api_get_observation(station_id, token)
    cache[cache_id] = ObservationResponse(**result)
    if ctx:
        await ctx.report_progress(progress=1, total=1)
    return cache[cache_id]


@mcp.tool(
    tags={"weather", "stations"},
    annotations={
        "title": "Get Weather Stations",
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
    },
    output_schema=_STATIONS_SCHEMA,
)
async def get_stations(
    ctx: Context | None = None,
) -> dict:
    """List the user's weather stations along with each station's location,
    devices, and capabilities.

    Use when: you need a station_id and don't have one. Always call this first
    if no station_id has appeared in the conversation. The response also
    covers most "what stations / where / what devices" questions without a
    follow-up call to get_station_details.

    Don't use for: current conditions (-> get_observation) or forecasts
    (-> get_forecast).

    Output: list of stations with id, name, location (lat, lon, timezone),
    devices, and capabilities. Admin/internal fields are excluded.
    """

    async def _work() -> dict:
        data = await _get_stations_data(ctx)
        return data.model_dump(exclude=_STATIONS_EXCLUDE)

    return await _dispatch(_work)


@mcp.tool(
    tags={"weather", "stations"},
    annotations={
        "title": "Get Weather Station Information",
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
    },
    output_schema=_STATION_SCHEMA,
)
async def get_station_details(
    station_id: Annotated[int, Field(description="The station ID to get information for", gt=0)],
    ctx: Context | None = None,
) -> dict:
    """Get configuration, devices, hardware, and location for one specific station.

    Use when: user asks about station hardware ("what devices does my station
    have"), location ("where is my station", "elevation", "what's my
    timezone"), or station-level metadata.

    Don't use for: weather data (-> get_observation, -> get_forecast). Don't
    use to find a station_id — that comes from get_stations.

    Workflow: requires station_id from get_stations.

    Output: detailed station record — devices, sensor capabilities, location,
    metadata. Rarely needed if the user only asked about weather.
    """

    async def _work() -> dict:
        data = await _get_station_details_data(station_id, ctx)
        return data.model_dump(exclude=_STATION_EXCLUDE)

    return await _dispatch(_work)


@mcp.tool(
    tags={"weather", "forecast"},
    annotations={
        "title": "Get Weather Forecast for a Station",
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
    },
    output_schema=_FORECAST_SCHEMA,
)
async def get_forecast(
    station_id: Annotated[
        int, Field(description="The ID of the station to get forecast for", gt=0)
    ],
    hours: Annotated[
        int,
        Field(
            default=12,
            description=(
                "Number of hourly forecasts to return (default: 12, max ~48)."
                " Capped at 6 in summary mode."
            ),
            ge=1,
            le=48,
        ),
    ] = 12,
    days: Annotated[
        int,
        Field(
            default=5,
            description=(
                "Number of daily forecasts to return (default: 5, max ~10)."
                " Capped at 2 in summary mode."
            ),
            ge=1,
            le=10,
        ),
    ] = 5,
    detailed: Annotated[
        bool,
        Field(
            default=False,
            description="If true, return full response. Default returns a condensed summary.",
        ),
    ] = False,
    ctx: Context | None = None,
) -> dict:
    """Get the weather forecast for a station — includes a current snapshot
    plus hourly and daily forecasts.

    Use when: user asks about future weather ("will it rain tomorrow", "this
    weekend", "10-day forecast", "next few hours").

    Don't use for: current-only questions when get_observation will do — this
    returns a much larger response. If you need both current AND future, this
    tool covers both in one call.

    Parameters: hours (1-48), days (1-10), detailed (default False). In
    summary mode the response is capped to 6 hourly and 2 daily entries
    regardless of hours/days; pass detailed=True to use the full ranges.

    Workflow: requires station_id from get_stations.

    Output: current snapshot + hourly + daily forecasts in the station's
    configured units — read 'units' in the response.
    """

    async def _work() -> dict:
        data = await _get_forecast_data(station_id, ctx)
        result = data.model_dump(exclude=_FORECAST_EXCLUDE)

        if detailed:
            result["forecast"]["hourly"] = result["forecast"]["hourly"][:hours]
            result["forecast"]["daily"] = result["forecast"]["daily"][:days]
        else:
            result["forecast"]["hourly"] = result["forecast"]["hourly"][: min(hours, 6)]
            result["forecast"]["daily"] = result["forecast"]["daily"][: min(days, 2)]
            for key in ("latitude", "longitude", "timezone_offset_minutes"):
                result.pop(key, None)

        return result

    return await _dispatch(_work)


@mcp.tool(
    tags={"weather", "observations"},
    annotations={
        "title": "Get Current Weather Observations for a Station",
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
    },
    output_schema=_OBSERVATION_SCHEMA,
)
async def get_observation(
    station_id: Annotated[
        int, Field(description="The ID of the station to get observations for", gt=0)
    ],
    detailed: Annotated[
        bool,
        Field(
            default=False,
            description="If true, return full response. Default returns a condensed summary.",
        ),
    ] = False,
    ctx: Context | None = None,
) -> dict:
    """Get the most recent weather observations from a station — current
    conditions including temperature, humidity, pressure, wind, precipitation,
    solar/UV, and lightning.

    Use when: the user asks about right-now conditions ("how warm is it",
    "is it raining", "any lightning"). Lighter and faster than get_forecast
    for current-only questions.

    Don't use for: future weather (-> get_forecast). Don't pass detailed=True
    unless the user explicitly asks for full sensor data (heat index, wet
    bulb, air density, etc.) — the default summary is what most answers need.

    Workflow: requires station_id from get_stations.

    Output: current observations in the station's configured units — read
    'station_units' in the response.
    """

    async def _work() -> dict:
        data = await _get_observation_data(station_id, ctx)
        result = data.model_dump(exclude=_OBSERVATION_EXCLUDE)

        if not detailed:
            for obs in result["obs"]:
                for field_name in _OBSERVATION_SUMMARY_FIELDS:
                    obs.pop(field_name, None)
            for key in ("latitude", "longitude", "elevation", "is_public"):
                result.pop(key, None)

        return result

    return await _dispatch(_work)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for monitoring."""
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    mcp.run()
