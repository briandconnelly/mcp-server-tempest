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
        Per-token JSON files under
        platformdirs.user_cache_dir("mcp-server-tempest").
        Used by tempest_get_stations and tempest_get_station_details.

Example Usage:
    # Get available stations
    stations = await client.call_tool("tempest_get_stations")

    # Get current conditions for a specific station
    conditions = await client.call_tool("tempest_get_observation", {"station_id": 12345})

    # Get the forecast
    forecast = await client.call_tool("tempest_get_forecast", {"station_id": 12345})
"""

import hashlib
import json
import logging
import os
import traceback
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version
from typing import Annotated, Any, TypeVar

from cachetools import TTLCache
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from .cache import DiskCache
from .errors import ErrorCode, WeatherFlowError, _new_request_id
from .middleware import TempestContractMiddleware
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

# Capability fingerprint source. Read directly from the installed dist-info,
# not from `__init__.__version__`, because `__init__` imports `server.mcp` and
# the reverse import would be circular. Falls back to "unknown" when the
# package is not installed (e.g. running from a source checkout without
# `uv sync` / `pip install -e .`).
try:
    _PKG_VERSION = version("mcp-server-tempest")
except PackageNotFoundError:
    _PKG_VERSION = "unknown"


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


_INSTRUCTIONS = """\
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
- "How many / list my stations"              -> tempest_get_stations
- "Deeper config / hardware for one station" -> tempest_get_station_details(station_id)
- "Current conditions / right now"           -> tempest_get_observation(station_id)
- "Forecast / later / tomorrow / this week"  -> tempest_get_forecast(station_id)

NOTES:
- Units follow each station's config — read 'station_units' / 'units' fields.
  Never assume °F vs °C or mph vs km/h.
- tempest_get_stations already returns devices and capabilities — only call
  tempest_get_station_details for the deeper per-station record.
- tempest_get_forecast also returns a current snapshot, but tempest_get_observation is
  lighter for current-only questions.
- tempest_get_forecast in summary mode (default) caps at 6 hourly / 2 daily; pass
  detailed=True for full ranges. The response carries `truncated`,
  `requested_*`, `returned_*`, and `truncation_hint` so clients can
  detect clipping structurally.

AMBIENT STATE (affects freshness and cache repair):
- WEATHERFLOW_CACHE_TTL (default 300s) and WEATHERFLOW_CACHE_SIZE
  (default 100): in-memory cache used by all four tools.
- WEATHERFLOW_DISK_CACHE_TTL (default 86400s): disk cache for
  tempest_get_stations and tempest_get_station_details only. Survives restarts; per-token
  subdirectory (hash-keyed for account isolation) under
  platformdirs.user_cache_dir("mcp-server-tempest").
- To force fresh data: restart the server (clears in-memory) or delete
  the cache directory above (clears disk).

TYPICAL WORKFLOW:
1. If you don't already have a station_id, call tempest_get_stations first.
   Station ids are not guessable — don't fabricate one.
2. Then tempest_get_observation(station_id) or tempest_get_forecast(station_id).
   If tempest_get_stations returned one station, use it without asking.

SETUP (required):
- WEATHERFLOW_API_TOKEN — get one at https://tempestwx.com/settings/tokens.

SERVER SURFACE: mcp-server-tempest@{version}. Read tempest://capabilities for
the structured surface summary (scope, tools, error codes, fingerprint). Each
tool result also carries _meta.fingerprint; it changes on any tool/schema/
error-code/instructions change.

TRANSPORT: stdio. The packaged entry point `mcp-server-tempest` (e.g. via
`uvx`) speaks MCP over stdio.
""".format(version=_PKG_VERSION)

# Create the MCP server
mcp = FastMCP(
    name="WeatherFlow Tempest",
    instructions=_INSTRUCTIONS,
    lifespan=lifespan,
    on_duplicate="error",
)
mcp.add_middleware(TempestContractMiddleware())


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


def _lock_additional_properties(obj: Any) -> None:
    """Recursively fill in ``additionalProperties: false`` on every object
    schema that does not already declare a value for ``additionalProperties``.

    The conditional guard preserves explicit declarations: a future model
    with ``model_config = ConfigDict(extra="allow")`` would cause Pydantic
    to emit ``additionalProperties: true`` in the generated schema, and
    that intent should survive the lockdown. Today no model opts in (and
    ``test_runtime_models_remain_permissive`` asserts ``extra="ignore"``
    everywhere), so the helper acts as a default-filling pass on every
    object schema in practice.

    Locks the published JSON Schema (output contract) without touching the
    runtime Pydantic models — those keep their default ``extra="ignore"`` so
    benign upstream additions to the WeatherFlow API still parse cleanly and
    are dropped on serialization. Drift detection happens on what we emit,
    not what we ingest.
    """
    if isinstance(obj, dict):
        if obj.get("type") == "object" and "additionalProperties" not in obj:
            obj["additionalProperties"] = False
        for value in obj.values():
            _lock_additional_properties(value)
    elif isinstance(obj, list):
        for item in obj:
            _lock_additional_properties(item)


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

    Also locks every object schema with ``additionalProperties: false`` so
    clients can detect drift if a tool response sprouts a field that wasn't
    in the contract.
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

    _lock_additional_properties(schema)

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


def _compute_fingerprint() -> str:
    """Deterministic hash of the agent-visible authored surface.

    Covers: package version, wire tool names, output schemas, error codes, and
    the instructions text (scope/negative-scope/selection). Input schemas are
    NOT hashed directly — an input-contract change requires a version bump,
    which moves this fingerprint. Stated in capabilities.fingerprint_covers.
    """
    surface = json.dumps(
        {
            "version": _PKG_VERSION,
            "tools": sorted(
                [
                    "tempest_get_stations",
                    "tempest_get_station_details",
                    "tempest_get_observation",
                    "tempest_get_forecast",
                ]
            ),
            "output_schemas": {
                "stations": _STATIONS_SCHEMA,
                "station": _STATION_SCHEMA,
                "forecast": _FORECAST_SCHEMA,
                "observation": _OBSERVATION_SCHEMA,
            },
            "error_codes": sorted(c.value for c in ErrorCode),
            "instructions": _INSTRUCTIONS,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(surface.encode()).hexdigest()[:16]


_FINGERPRINT = _compute_fingerprint()


def _build_capabilities() -> dict:
    return {
        "name": "WeatherFlow Tempest",
        "version": _PKG_VERSION,
        "fingerprint": _FINGERPRINT,
        "fingerprint_covers": (
            "version, wire tool names, output schemas, error codes, instructions. "
            "Input-schema changes are reflected only via a version bump."
        ),
        "transport": "stdio",
        "scope": (
            "Read-only access to the user's own WeatherFlow Tempest station(s) — "
            "not a global weather service."
        ),
        "not_in_scope": [
            "Global, regional, or arbitrary-location weather — use a public weather API",
            "Air quality, pollen, smoke index",
            "Severe-weather alerts, radar imagery, watches/warnings",
            "Historical/archive analysis beyond the live API",
        ],
        "tools": [
            {
                "name": "tempest_get_stations",
                "purpose": "List the user's stations, devices, capabilities.",
            },
            {
                "name": "tempest_get_station_details",
                "purpose": "Deep config/hardware/location for one station.",
            },
            {
                "name": "tempest_get_observation",
                "purpose": "Current conditions for one station.",
            },
            {
                "name": "tempest_get_forecast",
                "purpose": "Hourly + daily forecast plus a current snapshot.",
            },
        ],
        "error_codes": sorted(c.value for c in ErrorCode),
        "timestamps": (
            "Upstream weather timestamps are Unix epoch seconds, as provided by "
            "WeatherFlow; interpret local-time fields with the station's IANA "
            "`timezone`. Server-generated timestamps (e.g. _meta.ts_retrieved) "
            "are RFC3339 UTC."
        ),
        "caching": (
            "In-memory (WEATHERFLOW_CACHE_TTL, default 300s) for all tools; disk "
            "(WEATHERFLOW_DISK_CACHE_TTL, default 86400s) for stations and "
            "station_details. Each tool result carries _meta.cache and "
            "_meta.ts_retrieved."
        ),
    }


@mcp.resource(
    "tempest://capabilities",
    name="Server capabilities",
    description="Structured summary: scope, negative scope, tools, error codes, fingerprint.",
    mime_type="application/json",
)
def capabilities() -> dict:
    return _build_capabilities()


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
    name="tempest_get_stations",
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
    """List the user's weather stations.

    Use when: station_id is unknown, or for general inventory ("what
    stations do I have", "where", "what devices"). Covers most
    inventory questions without a follow-up call to tempest_get_station_details.

    Don't use for: current conditions (-> tempest_get_observation) or forecasts
    (-> tempest_get_forecast).

    Output: list of stations with id, name, location (lat, lon, timezone),
    devices, and capabilities. Admin/internal fields are excluded.

    Errors:
    - auth_missing — WEATHERFLOW_API_TOKEN env var not set
    - auth_invalid — token rejected; regenerate at
      https://tempestwx.com/settings/tokens
    - auth_forbidden — token lacks access (scope or ownership)
    - invalid_argument — a parameter was malformed (wrong type, out of range, or
      unknown field); fix it and retry
    - rate_limited (temporary; retry after retry_after_ms)
    - upstream_unavailable (temporary; transient WeatherFlow outage)
    - upstream_invalid_response — WeatherFlow returned something unparseable
    - internal_error — server bug; report at
      https://github.com/briandconnelly/mcp-server-tempest/issues

    Scope: the user's own WeatherFlow Tempest station(s) only — not a global
    or arbitrary-location weather service.
    """

    async def _work() -> dict:
        data = await _get_stations_data(ctx)
        return data.model_dump(exclude=_STATIONS_EXCLUDE)

    return await _dispatch(_work)


@mcp.tool(
    name="tempest_get_station_details",
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

    Don't use for: weather data (-> tempest_get_observation, -> tempest_get_forecast).

    Workflow: requires station_id from tempest_get_stations.

    Output: detailed station record — devices, sensor capabilities, location,
    metadata. Rarely needed if the user only asked about weather.

    Errors:
    - auth_missing — WEATHERFLOW_API_TOKEN env var not set
    - auth_invalid — token rejected; regenerate at
      https://tempestwx.com/settings/tokens
    - auth_forbidden — token lacks access to this station; verify ownership
    - invalid_argument — a parameter was malformed (wrong type, out of range, or
      unknown field); fix it and retry
    - station_not_found — invalid station_id; call tempest_get_stations
    - rate_limited (temporary; retry after retry_after_ms)
    - upstream_unavailable (temporary; transient WeatherFlow outage)
    - upstream_invalid_response — WeatherFlow returned something unparseable
    - internal_error — server bug; report at
      https://github.com/briandconnelly/mcp-server-tempest/issues

    Scope: the user's own WeatherFlow Tempest station(s) only — not a global
    or arbitrary-location weather service.
    """

    async def _work() -> dict:
        data = await _get_station_details_data(station_id, ctx)
        return data.model_dump(exclude=_STATION_EXCLUDE)

    return await _dispatch(_work)


@mcp.tool(
    name="tempest_get_forecast",
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
            description="Hourly forecasts to return. Capped at 6 in summary mode.",
            ge=1,
            le=48,
        ),
    ] = 12,
    days: Annotated[
        int,
        Field(
            default=5,
            description="Daily forecasts to return. Capped at 2 in summary mode.",
            ge=1,
            le=10,
        ),
    ] = 5,
    detailed: Annotated[
        bool,
        Field(
            default=False,
            description="If true, return full response. Default is a condensed summary.",
        ),
    ] = False,
    ctx: Context | None = None,
) -> dict:
    """Get the weather forecast for a station — includes a current snapshot
    plus hourly and daily forecasts.

    Use when: user asks about future weather ("will it rain tomorrow", "this
    weekend", "10-day forecast", "next few hours").

    Don't use for: current-only questions when tempest_get_observation will do —
    this returns a much larger response. If you need both current AND
    future, this tool covers both in one call.

    Workflow: requires station_id from tempest_get_stations. Summary mode (default)
    caps at 6 hourly / 2 daily; pass detailed=True for full ranges. The
    response carries `truncated` and `truncation_hint` so clients can
    detect clipping without parsing this prose.

    Output: current snapshot + hourly + daily forecasts in the station's
    configured units — read 'units' in the response.

    Errors:
    - auth_missing — WEATHERFLOW_API_TOKEN env var not set
    - auth_invalid — token rejected; regenerate at
      https://tempestwx.com/settings/tokens
    - auth_forbidden — token lacks access to this station; verify ownership
    - invalid_argument — a parameter was malformed (wrong type, out of range, or
      unknown field); fix it and retry
    - station_not_found — invalid station_id; call tempest_get_stations
    - rate_limited (temporary; retry after retry_after_ms)
    - upstream_unavailable (temporary; transient WeatherFlow outage)
    - upstream_invalid_response — WeatherFlow returned something unparseable
    - internal_error — server bug; report at
      https://github.com/briandconnelly/mcp-server-tempest/issues

    Scope: the user's own WeatherFlow Tempest station(s) only — not a global
    or arbitrary-location weather service.
    """

    async def _work() -> dict:
        data = await _get_forecast_data(station_id, ctx)
        result = data.model_dump(exclude=_FORECAST_EXCLUDE, exclude_none=not detailed)

        if detailed:
            result["forecast"]["hourly"] = result["forecast"]["hourly"][:hours]
            result["forecast"]["daily"] = result["forecast"]["daily"][:days]
            summary_capped = False
        else:
            result["forecast"]["hourly"] = result["forecast"]["hourly"][: min(hours, 6)]
            result["forecast"]["daily"] = result["forecast"]["daily"][: min(days, 2)]
            for key in ("latitude", "longitude", "timezone_offset_minutes"):
                result.pop(key, None)
            summary_capped = hours > 6 or days > 2

        returned_hours = len(result["forecast"]["hourly"])
        returned_days = len(result["forecast"]["daily"])
        # `truncated` reflects the actual shortfall between returned and
        # requested, regardless of cause. This is honest to the field's
        # description: an upstream shortfall in detailed mode also flips it
        # true, even though no summary cap was involved. `truncation_hint`
        # is reserved for the summary-cap path because that's the only case
        # with an actionable repair (pass detailed=true).
        truncated = returned_hours < hours or returned_days < days

        result["truncated"] = truncated
        result["requested_hours"] = hours
        result["requested_days"] = days
        result["returned_hours"] = returned_hours
        result["returned_days"] = returned_days
        if summary_capped:
            result["truncation_hint"] = (
                "summary mode caps to 6 hourly / 2 daily; pass detailed=true for full ranges"
            )
        else:
            # Drop the optional hint key when summary caps were not the
            # cause; an upstream shortfall in detailed mode has no
            # actionable repair beyond what `requested_*`/`returned_*`
            # already convey.
            result.pop("truncation_hint", None)

        return result

    return await _dispatch(_work)


@mcp.tool(
    name="tempest_get_observation",
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
            description="If true, return full response. Default is a condensed summary.",
        ),
    ] = False,
    ctx: Context | None = None,
) -> dict:
    """Get the most recent weather observations from a station — current
    conditions including temperature, humidity, pressure, wind, precipitation,
    solar/UV, and lightning.

    Use when: the user asks about right-now conditions ("how warm is it",
    "is it raining", "any lightning"). Lighter and faster than tempest_get_forecast
    for current-only questions.

    Don't use for: future weather (-> tempest_get_forecast). Don't pass detailed=True
    unless the user explicitly asks for full sensor data (heat index, wet
    bulb, air density, etc.) — the default summary is what most answers need.

    Workflow: requires station_id from tempest_get_stations.

    Output: current observations in the station's configured units — read
    'station_units' in the response.

    Errors:
    - auth_missing — WEATHERFLOW_API_TOKEN env var not set
    - auth_invalid — token rejected; regenerate at
      https://tempestwx.com/settings/tokens
    - auth_forbidden — token lacks access to this station; verify ownership
    - invalid_argument — a parameter was malformed (wrong type, out of range, or
      unknown field); fix it and retry
    - station_not_found — invalid station_id; call tempest_get_stations
    - rate_limited (temporary; retry after retry_after_ms)
    - upstream_unavailable (temporary; transient WeatherFlow outage)
    - upstream_invalid_response — WeatherFlow returned something unparseable
    - internal_error — server bug; report at
      https://github.com/briandconnelly/mcp-server-tempest/issues

    Scope: the user's own WeatherFlow Tempest station(s) only — not a global
    or arbitrary-location weather service.
    """

    async def _work() -> dict:
        data = await _get_observation_data(station_id, ctx)

        if detailed:
            result = data.model_dump(exclude=_OBSERVATION_EXCLUDE)
        else:
            result = data.model_dump(exclude=_OBSERVATION_EXCLUDE, exclude_none=True)
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
