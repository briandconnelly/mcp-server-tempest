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
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from time import time as _now
from typing import Annotated, Any, Generic, Literal, TypeVar

from cachetools import TTLCache
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.base import Tool, ToolResult
from fastmcp.utilities.json_schema import dereference_refs
from jsonschema import Draft202012Validator
from mcp.server.session import SUPPORTED_PROTOCOL_VERSIONS
from pydantic import BaseModel, Field

from .cache import DiskCache
from .errors import ErrorCode, WeatherFlowError, _new_request_id
from .middleware import JSON_SCHEMA_DIALECT, TempestContractMiddleware
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


# Fingerprint contract version. Bumped when the *inputs* to the hash change,
# so a client can tell "the surface changed" from "the server now measures the
# surface differently". Version 2 hashes complete wire records (see
# _compute_fingerprint); version 1 hashed a hand-enumerated field list that
# omitted tool descriptions and every resource record.
_FINGERPRINT_CONTRACT_VERSION = 2

# The MCP revision this server is authored and tested against, distinct from
# what any given session negotiates. `accepted_revisions` is read from the SDK
# rather than hardcoded so it cannot drift from what the server will actually
# accept: the session handler echoes the client's requested revision when it is
# supported and otherwise falls back to the SDK's latest. A plain import, so an
# SDK that moves this constant fails loudly at import instead of letting the
# server publish a revision list it does not honor.
_AUTHORED_PROTOCOL_TARGET = "2025-11-25"

_MCP_PROTOCOL: dict = {
    "authored_target": _AUTHORED_PROTOCOL_TARGET,
    "accepted_revisions": sorted(SUPPORTED_PROTOCOL_VERSIONS),
    "extensions": [],
    "negotiated_value_is_authoritative": (
        "The per-session revision is whatever `initialize` returned in "
        "InitializeResult.protocolVersion; this object declares the authored "
        "target and the full accepted set, not the active session's revision."
    ),
}


_KNOWN_CODES: frozenset[str] = frozenset(c.value for c in ErrorCode)


def _parse_structured_tool_error(te: ToolError) -> dict[str, Any] | None:
    """Return the parsed payload if the ToolError message is JSON with a
    known code, else None.

    `WeatherFlowError.to_tool_result` no longer raises ToolError, so this is
    a defensive parse for any ToolError a future helper or framework path
    might still raise directly; anything else is unstructured and must not
    bypass _dispatch's wire-contract enforcement.
    """
    if not te.args:
        return None
    try:
        payload = json.loads(te.args[0])
    except (TypeError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict) and payload.get("code") in _KNOWN_CODES:
        return payload
    return None


async def _dispatch(work: Callable[[], Awaitable[ToolResult]]) -> ToolResult:
    """Run a tool body. Convert WeatherFlowError → a ToolResult carrying the
    structured envelope in both structuredContent and a content[0].text JSON
    mirror; pass through ToolErrors that already carry a structured payload
    the same way; convert everything else (including unstructured
    ToolErrors) → internal_error. Always log with rid.
    """
    rid = _new_request_id()
    try:
        return await work()
    except WeatherFlowError as wfe:
        logger.warning("rid=%s code=%s msg=%s", rid, wfe.code.value, wfe.message)
        return wfe.to_tool_result(rid)
    except ToolError as te:
        # Pass through ONLY if already structured. Plain ToolError("text") from
        # a helper or future framework path would otherwise leak as unstructured
        # text and defeat the wire contract; wrap it as internal_error instead.
        payload = _parse_structured_tool_error(te)
        if payload is not None:
            # Log the payload's own request_id (what the client actually
            # sees), not the rid generated above for this dispatch — the
            # payload was built by whatever raised the pre-structured error.
            logger.debug(
                "rid=%s passing through pre-structured ToolError",
                payload.get("request_id", rid),
            )
            return ToolResult(content=te.args[0], structured_content=payload, is_error=True)
        logger.error("rid=%s caught unstructured ToolError: %r", rid, te.args)
        wfe = WeatherFlowError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Unexpected server error.",
            hint=f"Check server logs for request_id={rid}.",
        )
        return wfe.to_tool_result(rid)
    except Exception as exc:
        logger.error("rid=%s unexpected: %s\n%s", rid, exc, traceback.format_exc())
        wfe = WeatherFlowError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Unexpected server error.",
            hint=f"Check server logs for request_id={rid}.",
        )
        return wfe.to_tool_result(rid)


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


# Values are the four response models; typed Any because each entry site
# narrows to its concrete model and a BaseModel bound would force casts at
# every read.
cache: TTLCache[str, Any] = TTLCache(
    maxsize=_int_env("WEATHERFLOW_CACHE_SIZE", 100),
    ttl=_int_env("WEATHERFLOW_CACHE_TTL", 300),
)

# Epoch seconds of the last upstream fetch per cache key. A bounded TTLCache
# (same shape as the data cache) so it cannot leak relative to it; if an entry
# expires before its data, ts_retrieved is simply omitted on that hit.
_fetch_times: TTLCache[str, float] = TTLCache(
    maxsize=_int_env("WEATHERFLOW_CACHE_SIZE", 100),
    ttl=_int_env("WEATHERFLOW_CACHE_TTL", 300),
)


@dataclass
class Fetched(Generic[T]):
    """A model plus where it came from, for response _meta."""

    data: T
    cache: Literal["memory", "disk", "miss"]
    ts_epoch: float | None


def _iso(ts_epoch: float | None) -> str | None:
    return None if ts_epoch is None else datetime.fromtimestamp(ts_epoch, tz=UTC).isoformat()


# All convention metadata on tool results lives under this single prefixed
# _meta key (MCP reserves unprefixed _meta names for the protocol; the
# reverse-DNS prefix is the spec's collision guard). Grouped under one key
# rather than three prefixed siblings to keep payloads and the capability
# prose compact.
_META_KEY = "net.bconnelly.tempest/fetch"


def _meta_for(fetched: Fetched) -> dict:
    fetch_meta: dict = {
        "cache": fetched.cache,
        "fingerprint": _FINGERPRINT,
        "fingerprint_contract_version": _FINGERPRINT_CONTRACT_VERSION,
    }
    iso = _iso(fetched.ts_epoch)
    if iso is not None:
        fetch_meta["ts_retrieved"] = iso
    return {_META_KEY: fetch_meta}


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
            hit = dc.get_with_age("stations", StationsResponse)
            if hit is not None:
                model, ts = hit
                cache["stations"] = model
                _fetch_times["stations"] = ts
                logger.info(
                    "Pre-warmed stations cache from disk (%d stations)",
                    len(model.stations),
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
- "What can this server do"                  -> tempest_get_capabilities

NOTES:
- Units follow each station's config — read 'station_units' / 'units' fields.
  Never assume °F vs °C or mph vs km/h.
- tempest_get_stations returns devices but NOT sensor capabilities (upstream
  omits them from the station list, so the field is absent from its schema
  and its responses). For "what can my station measure", call
  tempest_get_station_details(station_id) — it is the only tool that returns
  the `capabilities` list.
- tempest_get_forecast also returns a current snapshot, but tempest_get_observation is
  lighter for current-only questions.
- tempest_get_forecast returns 6 hourly / 2 daily unless you pass hours/days.
  Entry counts come from hours/days alone; detailed=True adds field density
  (null fields, station coordinates) and never changes how many entries come
  back. The response carries `truncated`, `requested_*`, `returned_*`, and
  `truncation_hint` so clients can detect an upstream shortfall structurally.

AMBIENT STATE (affects freshness and cache repair):
- WEATHERFLOW_CACHE_TTL (default 300s) and WEATHERFLOW_CACHE_SIZE
  (default 100): in-memory cache used by every tool that fetches upstream
  (tempest_get_capabilities is static and uses no cache).
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

SERVER SURFACE: mcp-server-tempest@{version}. Read tempest://capabilities (or
call tempest_get_capabilities if your client does not expose MCP resources)
for the structured surface summary (scope, tools, error codes, fingerprint).
Each tool result also carries the fingerprint in
_meta["net.bconnelly.tempest/fetch"], beside fingerprint_contract_version.
The fingerprint hashes the complete wire record of every tool and resource —
descriptions included — plus error codes, instructions, the protocol
contract, and the capability contract, so any change an agent could plan
against moves it.

TRANSPORT: stdio. The packaged entry point `mcp-server-tempest` (e.g. via
`uvx`) speaks MCP over stdio.

PROTOCOL: authored and tested against MCP {protocol_target}; the server also
accepts {accepted_revisions}. The revision in force for your session is
whatever `initialize` returned in InitializeResult.protocolVersion — that
value, not this line, is authoritative for the active session.
""".format(
    version=_PKG_VERSION,
    protocol_target=_AUTHORED_PROTOCOL_TARGET,
    accepted_revisions=", ".join(sorted(SUPPORTED_PROTOCOL_VERSIONS)),
)

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


def _strip_titles(obj: Any) -> None:
    """Recursively delete every ``title`` annotation from a JSON Schema tree.

    Pydantic emits a ``title`` on every property and ``$defs`` entry, each a
    title-cased echo of the field/model name (``air_temperature`` ->
    "Air Temperature", ``uv`` -> "Uv"). Titles carry no validation semantics
    and add nothing an agent can't read off the field name, yet they account
    for ~16% of the published output-schema bytes that clients pay for on
    ``tools/list``. Stripping them is the largest validation-safe lever for
    shrinking the tool catalog (see issue #69). Interpretive ``description``
    strings are deliberately left untouched.

    Only the JSON Schema ``title`` *keyword* (a string annotation) is removed.
    A model field literally named ``title`` appears as ``properties["title"]``
    whose value is a schema (a dict), so guarding on ``str`` preserves it
    instead of deleting the whole property.
    """
    if isinstance(obj, dict):
        if isinstance(obj.get("title"), str):
            del obj["title"]
        for value in obj.values():
            _strip_titles(value)
    elif isinstance(obj, list):
        for item in obj:
            _strip_titles(item)


def _refs_in(obj: Any) -> set[str]:
    """Every ``#/$defs/<name>`` target referenced anywhere under ``obj``.

    Descends into a ``$defs`` container's *members* only when ``obj`` is that
    member — the top-level call is handed a root with ``$defs`` stripped, so
    reachability starts from the schema proper rather than from every
    definition trivially referencing itself.
    """
    found: set[str] = set()
    if isinstance(obj, dict):
        ref = obj.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            found.add(ref.removeprefix("#/$defs/"))
        for key, value in obj.items():
            if key != "$defs":
                found |= _refs_in(value)
    elif isinstance(obj, list):
        for item in obj:
            found |= _refs_in(item)
    return found


def _prune_unreferenced_defs(schema: dict) -> None:
    """Drop ``$defs`` entries nothing reaches, transitively.

    Omitting a property (see ``omitted_fields`` below) can orphan the
    definitions it alone referenced. Leaving them behind would publish a
    sub-schema for data the tool cannot return — the same
    schema-contradicts-behavior defect omission is meant to fix — and would
    bill every client for the bytes on ``tools/list``.
    """
    defs = schema.get("$defs")
    if not defs:
        return

    reachable = _refs_in({k: v for k, v in schema.items() if k != "$defs"})
    frontier = set(reachable)
    while frontier:
        discovered: set[str] = set()
        for name in frontier:
            if name in defs:
                discovered |= _refs_in(defs[name]) - reachable
        reachable |= discovered
        frontier = discovered

    for name in set(defs) - reachable:
        del defs[name]
    if not defs:
        del schema["$defs"]


def _relaxed_schema(
    model_class: type[BaseModel],
    optional_fields: dict[str, set[str]],
    omitted_fields: dict[str, set[str]] | None = None,
) -> dict:
    """Generate a JSON schema where only specified fields are made non-required.

    Args:
        model_class: The Pydantic model to generate the schema from.
        optional_fields: Mapping of schema definition name (or "$root" for the
            top-level object) to the set of field names that should be removed
            from that definition's ``required`` list.
        omitted_fields: Same mapping shape, but the named properties are
            deleted from the schema outright rather than merely made optional.
            Use this where a tool can *never* populate a field its model
            declares, so the published contract does not advertise data the
            handler always drops. The handler's ``exclude`` set must omit the
            same fields, or the response fails output validation against the
            locked (``additionalProperties: false``) schema.

    Strips redundant Pydantic ``title`` annotations (see :func:`_strip_titles`)
    and locks every object schema with ``additionalProperties: false`` so
    clients can detect drift if a tool response sprouts a field that wasn't
    in the contract.
    """
    schema = model_class.model_json_schema(mode="serialization")

    def _relax(obj: dict, name: str) -> None:
        fields = optional_fields.get(name, set())
        if fields and "required" in obj:
            obj["required"] = [r for r in obj["required"] if r not in fields]

    def _omit(obj: dict, name: str) -> None:
        fields = (omitted_fields or {}).get(name, set())
        if not fields:
            return
        properties = obj.get("properties", {})
        for field_name in fields:
            properties.pop(field_name, None)
        if "required" in obj:
            obj["required"] = [r for r in obj["required"] if r not in fields]

    # Top-level
    _relax(schema, "$root")
    _omit(schema, "$root")

    # $defs
    for def_name, defn in schema.get("$defs", {}).items():
        _relax(defn, def_name)
        _omit(defn, def_name)

    _prune_unreferenced_defs(schema)
    _strip_titles(schema)
    _lock_additional_properties(schema)

    # Stamp the dialect at generation time (not only via the on_list_tools
    # middleware) so the advertised output schema and the fingerprinted schema
    # are identical — the fingerprint genuinely covers the declared dialect.
    schema["$schema"] = JSON_SCHEMA_DIALECT

    return schema


# `capabilities` is omitted outright rather than merely relaxed: upstream's
# `GET /stations` never populates it (only `GET /stations/{id}` does), so
# publishing it here would advertise data this tool cannot return and point
# agents at the wrong tool for "what can my station measure". The
# WeatherStation model keeps the field because StationResponse subclasses it
# and tempest_get_station_details genuinely returns it. Dropping the property
# orphans the StationCapability definition, which _prune_unreferenced_defs
# then removes from this schema only.
_STATIONS_SCHEMA = _relaxed_schema(
    StationsResponse,
    {
        "WeatherStation": {
            "created_epoch",
            "last_modified_epoch",
        },
        "StationMeta": {"share_with_wf", "share_with_wu"},
        "StationItem": {"station_item_id", "location_id", "location_item_id"},
    },
    omitted_fields={"WeatherStation": {"capabilities"}},
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


# Output schema for tempest_get_capabilities. Deliberately permissive
# (additionalProperties: true): the capability summary grows additively, and
# new informational fields must not be a breaking change for clients that
# validate against this schema. Only the keys agents branch on are required.
_CAPABILITIES_OUTPUT_SCHEMA: dict = {
    "$schema": JSON_SCHEMA_DIALECT,
    "type": "object",
    "additionalProperties": True,
    "required": [
        "name",
        "scope",
        "not_in_scope",
        "tools",
        "error_codes",
        "version",
        "fingerprint",
        "fingerprint_contract_version",
    ],
    "properties": {
        "name": {"type": "string"},
        "transport": {"type": "string"},
        "scope": {"type": "string"},
        "not_in_scope": {"type": "array", "items": {"type": "string"}},
        "tools": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "required": ["name", "purpose"],
                "properties": {
                    "name": {"type": "string"},
                    "purpose": {"type": "string"},
                },
            },
        },
        "error_codes": {"type": "array", "items": {"type": "string"}},
        "version": {"type": "string"},
        "fingerprint": {"type": "string"},
        "fingerprint_contract_version": {"type": "integer"},
    },
}


# Static, agent-visible capability contract. Folded into the fingerprint (see
# _compute_fingerprint) so any change to this prose — scope, negative scope,
# tool purposes, the error envelope — moves the fingerprint, and served
# verbatim by the tempest://capabilities resource. Excludes the
# self-referential `fingerprint` and the already-fingerprinted `version` /
# `error_codes`, which _build_capabilities() adds back at serve time.
_CAPABILITY_CONTRACT: dict = {
    "name": "WeatherFlow Tempest",
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
            "purpose": "List the user's stations, locations, devices.",
        },
        {
            "name": "tempest_get_station_details",
            "purpose": (
                "Deep config/hardware/location for one station, plus the "
                "sensor capabilities the station list omits."
            ),
        },
        {
            "name": "tempest_get_observation",
            "purpose": "Current conditions for one station.",
        },
        {
            "name": "tempest_get_forecast",
            "purpose": "Hourly + daily forecast plus a current snapshot.",
        },
        {
            "name": "tempest_get_capabilities",
            "purpose": (
                "Structured surface summary; mirrors the tempest://capabilities "
                "resource for clients without resource support."
            ),
        },
    ],
    "error_channel": (
        "Errors arrive as an isError tool result. The JSON envelope — {code, "
        "message, temporary, request_id} plus optional hint, field, value, "
        "next, retry_after_ms, details — is in `structuredContent`, with an "
        "identical compact-JSON copy in `content[0].text` for clients that "
        "only read text content. Branch on `code` (see error_codes), not "
        "`message`; treat an unrecognized `code` as a generic failure (codes "
        "are added additively). Optional fields are omitted when absent. "
        "`retry_after_ms` is always present when `temporary` is true — a "
        "non-negative integer when the delay is known, else null (retry "
        "with backoff); it is omitted when `temporary` is false, unless a "
        "caller explicitly sets one (no error path does today)."
    ),
    "fingerprint_covers": (
        "Everything an agent can plan against: version, the complete wire "
        "record of every tool (name, title, description, input schema, output "
        "schema, annotations, _meta) exactly as tools/list returns it, the "
        "complete record of every resource as resources/list returns it, error "
        "codes, instructions, the protocol contract, and this capability "
        "contract. Because whole records are hashed rather than a field list, "
        "fields the MCP types gain later are covered automatically. Read "
        "fingerprint_contract_version alongside the fingerprint: it identifies "
        "WHAT is hashed, so a change to it means the surface is measured "
        "differently, not that the surface itself changed."
    ),
    "protocol": _MCP_PROTOCOL,
    "latency": (
        "Each tool makes at most one upstream WeatherFlow call with a 15s total "
        "timeout; a breach returns upstream_unavailable (temporary). Cached "
        "reads return immediately."
    ),
    "timestamps": (
        "Upstream weather timestamps are Unix epoch seconds, as provided by "
        "WeatherFlow; interpret local-time fields with the station's IANA "
        "`timezone`. Server-generated timestamps (e.g. ts_retrieved in "
        '_meta["net.bconnelly.tempest/fetch"]) are RFC3339 UTC.'
    ),
    "caching": (
        "In-memory (WEATHERFLOW_CACHE_TTL, default 300s) for every tool that "
        "fetches upstream (stations, station_details, observation, forecast); "
        "stations and station_details additionally use a disk cache "
        "(WEATHERFLOW_DISK_CACHE_TTL, default 86400s). Each fetching tool's "
        'result carries cache provenance under _meta["net.bconnelly.tempest/'
        'fetch"]: {cache, fingerprint, fingerprint_contract_version, '
        "ts_retrieved}; ts_retrieved is included when the fetch time is known "
        "(it may be omitted on some cache hits). tempest_get_capabilities is "
        "static — no upstream fetch or cache — so its _meta carries only "
        "{fingerprint, fingerprint_contract_version}."
    ),
}


def _local_tool_components() -> dict[str, Tool]:
    """Registered Tool components keyed by wire name, from the local registry.

    Reads FastMCP's private local component registry synchronously — the public
    list_tools() API is async and unusable at import time. Raises if the
    registry has moved (a FastMCP upgrade) or is empty, so the capability
    fingerprint fails loudly instead of silently hashing the wrong contract.
    """
    try:
        components = mcp._local_provider._components  # noqa: SLF001
    except AttributeError as exc:
        raise RuntimeError(
            "FastMCP's local tool registry has moved; cannot compute the "
            "capability fingerprint. Update _local_tool_components for this "
            "FastMCP version."
        ) from exc
    tools = {c.name: c for c in components.values() if isinstance(c, Tool)}
    if not tools:
        raise RuntimeError(
            "FastMCP local tool registry is empty; cannot compute the capability fingerprint."
        )
    return tools


def _to_wire_schema_form(record: dict) -> dict:
    """Put a record's schemas into the exact form clients receive, in place.

    Two serve-time transforms stand between a registered component and the
    wire, and the fingerprint is only honest if it hashes the far side of
    both:

    1. FastMCP's dereference middleware (on by default,
       ``FastMCP(dereference_schemas=True)``) inlines every ``$ref`` so the
       published schema is self-contained. ``to_mcp_tool()`` does not — it
       still carries ``$defs``.
    2. TempestContractMiddleware.on_list_tools stamps the JSON Schema dialect.
       It mutates the live component dicts, so applying the same setdefault
       here also keeps _compute_fingerprint() idempotent across the first
       tools/call — otherwise the pre- and post-middleware hashes would
       differ.

    test_fingerprinted_tool_records_match_list_tools compares the result
    byte-for-byte against list_tools(), so if a FastMCP upgrade moves either
    transform this fails loudly instead of hashing a shape no client sees.
    """
    for key in ("inputSchema", "outputSchema"):
        schema = record.get(key)
        if isinstance(schema, dict):
            schema = dereference_refs(schema)
            schema.setdefault("$schema", JSON_SCHEMA_DIALECT)
            record[key] = schema
    return record


def _wire_tool_records() -> dict[str, dict]:
    """Complete `Tool` records for every registered tool, as clients receive
    them from tools/list.

    Hashing the whole canonical record — rather than a hand-picked list of
    fields — is what makes the fingerprint's coverage claim honest. It sweeps
    in name, title, description, inputSchema, outputSchema, annotations, and
    `_meta` together, and it keeps covering fields the MCP `Tool` type gains
    later (icons, execution metadata) without anyone remembering to extend
    this function. Contract version 1 enumerated fields by hand and silently
    omitted tool descriptions, the primary input to tool selection.

    Tests compare this against mcp.list_tools() so registry or serialization
    drift fails loudly.
    """
    return {
        name: _to_wire_schema_form(
            component.to_mcp_tool().model_dump(exclude_none=True, mode="json", by_alias=True)
        )
        for name, component in _local_tool_components().items()
    }


def _wire_resource_records() -> dict[str, dict]:
    """Complete `Resource` records, keyed by URI, as clients receive them from
    resources/list.

    The resource catalog is agent-visible surface too: renaming
    tempest://capabilities or rewriting its description changes what an agent
    plans against. Contract version 1 hashed no resource record at all, so
    either edit was invisible to a fingerprint-caching client.
    """
    records: dict[str, dict] = {}
    for component in mcp._local_provider._components.values():  # noqa: SLF001
        to_mcp_resource = getattr(component, "to_mcp_resource", None)
        if to_mcp_resource is None:
            continue
        record = to_mcp_resource().model_dump(exclude_none=True, mode="json", by_alias=True)
        records[str(record["uri"])] = record
    return records


def _require_tool_descriptions(records: dict[str, dict]) -> None:
    """Refuse to publish a catalog whose tools have no descriptions.

    Tool descriptions come from docstrings, which `python -OO` discards. An
    -OO run therefore serves every tool with its primary selection guidance
    missing — an agent choosing between five same-prefixed weather tools gets
    names and schemas only. That is a worse failure than not starting, and it
    is silent: the catalog still validates and the tools still work.

    Never paper over it by substituting a placeholder or normalizing the
    missing description away before hashing. Absent descriptions ARE a
    different agent-visible surface, so a fingerprint that hid the difference
    would be lying about what the client received.
    """
    undescribed = sorted(name for name, record in records.items() if not record.get("description"))
    if undescribed:
        raise RuntimeError(
            "Tools are missing descriptions: "
            f"{', '.join(undescribed)}. Tool descriptions come from docstrings; "
            "running under `python -OO` strips them and would serve a catalog "
            "agents cannot select from. Run without -OO."
        )


def _compute_fingerprint() -> str:
    """Deterministic hash of the agent-visible authored surface.

    Contract version 2 (see _FINGERPRINT_CONTRACT_VERSION). Hashes complete
    wire records — every `Tool` record from tools/list and every `Resource`
    record from resources/list — plus package version, error codes, the
    instructions text, the MCP protocol contract, and _CAPABILITY_CONTRACT.
    Hashing whole records rather than a hand-picked field list is what makes
    the coverage claim honest: tool descriptions, titles, `_meta`, and the
    resource catalog are all swept in, as is any field the MCP types gain
    later.

    Version 1 enumerated fields by hand and omitted tool descriptions (the
    primary input to tool selection) and every resource record. It justified
    the description exclusion as avoiding fingerprint churn on prose polish,
    which mistook the fingerprint doing its job for a cost: a changed
    selection document is exactly what a caching client must be told about.

    Output schemas are no longer hashed separately — each rides inside its
    tool's wire record, so the module-level _*_SCHEMA constants are covered
    via the records rather than by name.

    Must be called after all tools are registered: the records come from the
    live registry, so the _FINGERPRINT assignment sits at the end of this
    module.
    """
    tool_records = _wire_tool_records()
    _require_tool_descriptions(tool_records)
    surface = json.dumps(
        {
            "fingerprint_contract_version": _FINGERPRINT_CONTRACT_VERSION,
            "version": _PKG_VERSION,
            "tools": sorted(tool_records),
            "tool_records": tool_records,
            "resource_records": _wire_resource_records(),
            "error_codes": sorted(c.value for c in ErrorCode),
            "instructions": _INSTRUCTIONS,
            "protocol": _MCP_PROTOCOL,
            "capability_contract": _CAPABILITY_CONTRACT,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(surface.encode()).hexdigest()[:16]


# The server skips its own output validation when a ToolResult carries _meta,
# so we validate here against the same locked schemas before shipping. A
# failure means the response drifted from the published contract — a server
# bug, surfaced as internal_error rather than handed to the agent.
# values are Draft202012Validator; annotated Any because jsonschema ships no py.typed
_OUTPUT_VALIDATORS: dict[str, Any] = {
    "stations": Draft202012Validator(_STATIONS_SCHEMA),
    "station": Draft202012Validator(_STATION_SCHEMA),
    "forecast": Draft202012Validator(_FORECAST_SCHEMA),
    "observation": Draft202012Validator(_OBSERVATION_SCHEMA),
    "capabilities": Draft202012Validator(_CAPABILITIES_OUTPUT_SCHEMA),
}


def _validated(schema_key: str, result: dict, meta: dict) -> ToolResult:
    validator = _OUTPUT_VALIDATORS[schema_key]
    if not validator.is_valid(result):
        # str() each path element: paths mix str keys and int indices, and
        # sorting heterogeneous types would raise TypeError and mask the real
        # validation error.
        errs = sorted(
            validator.iter_errors(result),
            key=lambda e: [str(x) for x in e.path],
        )
        raise WeatherFlowError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Response failed output-schema validation.",
            hint="Server contract drift; report at "
            "https://github.com/briandconnelly/mcp-server-tempest/issues",
            details={"validation_error": errs[0].message},
        )
    return ToolResult(structured_content=result, meta=meta)


def _build_capabilities() -> dict:
    # The static contract (_CAPABILITY_CONTRACT) is fingerprinted; version,
    # fingerprint, and error_codes are stamped in at serve time. error_codes
    # is sorted here from the live ErrorCode enum (the fingerprint hashes the
    # same sorted list separately), so the two can never disagree.
    return {
        **_CAPABILITY_CONTRACT,
        "version": _PKG_VERSION,
        "fingerprint": _FINGERPRINT,
        "fingerprint_contract_version": _FINGERPRINT_CONTRACT_VERSION,
        "error_codes": sorted(c.value for c in ErrorCode),
    }


@mcp.resource(
    "tempest://capabilities",
    name="Server capabilities",
    description="Structured summary: scope, negative scope, tools, error codes, fingerprint.",
    mime_type="application/json",
)
def capabilities() -> dict:
    return _build_capabilities()


# `capabilities` is dropped wholesale here, matching its omission from
# _STATIONS_SCHEMA. Upstream's station-list payload carries no `capabilities`
# key at all; the model's `None` default materialized one, which we then
# serialized as `capabilities: null` — a value that reads as "this station
# reports no sensors" rather than "ask tempest_get_station_details", the tool
# that actually returns it.
_STATIONS_EXCLUDE: dict = {
    "stations": {
        "__all__": {
            "created_epoch": True,
            "last_modified_epoch": True,
            "capabilities": True,
            "station_meta": {"share_with_wf", "share_with_wu"},
            "station_items": {
                "__all__": {"station_item_id", "location_id", "location_item_id"},
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


async def _notify_info(ctx: Context | None, message: str) -> None:
    """Best-effort ctx.info. Progress/log notifications are advisory: a send
    failure (no client log capability, transport hiccup, disconnect) must never
    turn an otherwise-successful fetch into an internal_error."""
    if ctx is None:
        return
    try:
        await ctx.info(message)
    except Exception as exc:  # noqa: BLE001 - advisory notification, never fatal
        logger.debug("ctx.info notification dropped: %s", exc)


async def _notify_progress(ctx: Context | None, *, progress: float, total: float) -> None:
    """Best-effort ctx.report_progress; see _notify_info for the rationale."""
    if ctx is None:
        return
    try:
        await ctx.report_progress(progress=progress, total=total)
    except Exception as exc:  # noqa: BLE001 - advisory notification, never fatal
        logger.debug("ctx.report_progress notification dropped: %s", exc)


async def _get_stations_data(
    ctx: Context | None, use_cache: bool = True
) -> Fetched[StationsResponse]:
    """Shared logic for getting stations data."""
    token = _get_api_token()

    if use_cache and "stations" in cache:
        await _notify_info(ctx, "Using cached station data")
        return Fetched(cache["stations"], "memory", _fetch_times.get("stations"))

    dc = _get_disk_cache()
    if use_cache and dc:
        hit = dc.get_with_age("stations", StationsResponse)
        if hit is not None:
            model, ts = hit
            await _notify_info(ctx, "Using disk-cached station data")
            cache["stations"] = model
            _fetch_times["stations"] = ts
            return Fetched(model, "disk", ts)

    await _notify_progress(ctx, progress=0, total=1)
    await _notify_info(ctx, "Getting available stations via the Tempest API")
    result = await api_get_stations(token)
    cache["stations"] = StationsResponse(**result)
    _fetch_times["stations"] = _now()
    if dc:
        dc.set("stations", cache["stations"])
    await _notify_progress(ctx, progress=1, total=1)
    return Fetched(cache["stations"], "miss", _fetch_times["stations"])


async def _get_station_details_data(
    station_id: int, ctx: Context | None, use_cache: bool = True
) -> Fetched[StationResponse]:
    """Shared logic for getting station details data."""
    token = _get_api_token()

    cache_id = f"station_id_{station_id}"

    if use_cache and cache_id in cache:
        await _notify_info(ctx, f"Using cached station data for station {station_id}")
        return Fetched(cache[cache_id], "memory", _fetch_times.get(cache_id))

    dc = _get_disk_cache()
    if use_cache and dc:
        hit = dc.get_with_age(cache_id, StationResponse)
        if hit is not None:
            model, ts = hit
            await _notify_info(ctx, f"Using disk-cached station data for station {station_id}")
            cache[cache_id] = model
            _fetch_times[cache_id] = ts
            return Fetched(model, "disk", ts)

    await _notify_progress(ctx, progress=0, total=1)
    await _notify_info(ctx, f"Getting station ID data for station {station_id} via the Tempest API")
    result = await api_get_station_id(station_id, token)
    cache[cache_id] = StationResponse(**result)
    _fetch_times[cache_id] = _now()
    if dc:
        dc.set(cache_id, cache[cache_id])
    await _notify_progress(ctx, progress=1, total=1)
    return Fetched(cache[cache_id], "miss", _fetch_times[cache_id])


async def _get_forecast_data(
    station_id: int, ctx: Context | None, use_cache: bool = True
) -> Fetched[ForecastResponse]:
    """Shared logic for getting forecast data."""
    token = _get_api_token()

    cache_id = f"forecast_{station_id}"
    if use_cache and cache_id in cache:
        await _notify_info(ctx, f"Using cached forecast data for station {station_id}")
        return Fetched(cache[cache_id], "memory", _fetch_times.get(cache_id))

    await _notify_progress(ctx, progress=0, total=1)
    await _notify_info(ctx, f"Getting forecast for station {station_id} via the Tempest API")
    result = await api_get_forecast(station_id, token)
    cache[cache_id] = ForecastResponse(**result)
    _fetch_times[cache_id] = _now()
    await _notify_progress(ctx, progress=1, total=1)
    return Fetched(cache[cache_id], "miss", _fetch_times[cache_id])


async def _get_observation_data(
    station_id: int, ctx: Context | None, use_cache: bool = True
) -> Fetched[ObservationResponse]:
    """Shared logic for getting observation data."""
    token = _get_api_token()

    cache_id = f"observation_{station_id}"
    if use_cache and cache_id in cache:
        await _notify_info(ctx, f"Using cached observation data for station {station_id}")
        return Fetched(cache[cache_id], "memory", _fetch_times.get(cache_id))

    await _notify_progress(ctx, progress=0, total=1)
    await _notify_info(ctx, f"Getting observations for station {station_id} via the Tempest API")
    result = await api_get_observation(station_id, token)
    cache[cache_id] = ObservationResponse(**result)
    _fetch_times[cache_id] = _now()
    await _notify_progress(ctx, progress=1, total=1)
    return Fetched(cache[cache_id], "miss", _fetch_times[cache_id])


# Annotation policy, applied to every tool below. openWorldHint reflects the
# tool's interaction boundary, per the MCP tool-annotations guidance: the four
# WeatherFlow-backed tools reach an external service and return externally
# mutable data (live weather, station config that can change outside this
# server), so they are open-world (True); tempest_get_capabilities is static
# and local, so it stays closed-world (False). idempotentHint is omitted
# because the MCP spec defines it as meaningful only when readOnlyHint is false.
@mcp.tool(
    name="tempest_get_stations",
    tags={"weather", "stations"},
    annotations={
        "title": "Get Weather Stations",
        "readOnlyHint": True,
        "openWorldHint": True,
    },
    output_schema=_STATIONS_SCHEMA,
)
async def get_stations(
    ctx: Context | None = None,
) -> ToolResult:
    """List the user's weather stations.

    Use when: station_id is unknown, or for general inventory ("what
    stations do I have", "where", "what devices"). Covers most
    inventory questions without a follow-up call to tempest_get_station_details.

    Don't use for: current conditions (-> tempest_get_observation) or forecasts
    (-> tempest_get_forecast). Also not for sensor capabilities ("what can my
    station measure") — upstream does not supply them for the station list, so
    this tool does not return a `capabilities` field at all; call
    tempest_get_station_details(station_id) for that.

    Output: list of stations with id, name, location (lat, lon, timezone),
    and devices. Admin/internal fields are excluded.

    Errors:
    - auth_missing/auth_invalid/auth_forbidden — token not set, rejected,
      or lacking access; see the error's hint
    - rate_limited, upstream_unavailable (temporary; retry, honoring
      retry_after_ms when present)
    - Catalog: tempest_get_capabilities / tempest://capabilities
      (error_codes, error_channel); hint, when present, carries repair
      guidance

    Scope: the user's own WeatherFlow Tempest station(s) only — not a global
    or arbitrary-location weather service.
    """

    async def _work() -> ToolResult:
        fetched = await _get_stations_data(ctx)
        result = fetched.data.model_dump(exclude=_STATIONS_EXCLUDE)
        return _validated("stations", result, _meta_for(fetched))

    return await _dispatch(_work)


@mcp.tool(
    name="tempest_get_station_details",
    tags={"weather", "stations"},
    annotations={
        "title": "Get Weather Station Information",
        "readOnlyHint": True,
        "openWorldHint": True,
    },
    output_schema=_STATION_SCHEMA,
)
async def get_station_details(
    station_id: Annotated[int, Field(description="The station ID to get information for", gt=0)],
    ctx: Context | None = None,
) -> ToolResult:
    """Get configuration, devices, hardware, and location for one specific station.

    Use when: user asks what the station can measure ("does it track UV",
    "what sensors does it have") — this is the only tool that returns the
    `capabilities` list; tempest_get_stations does not return it at all.
    Also for station hardware, location ("where is my station", "elevation",
    "what's my timezone"), or station-level metadata.

    Don't use for: weather data (-> tempest_get_observation, -> tempest_get_forecast).

    Workflow: requires station_id from tempest_get_stations.

    Output: detailed station record — sensor capabilities, devices, location,
    metadata. Apart from `capabilities`, this repeats the matching
    tempest_get_stations entry; skip it if you already have that and don't
    need capabilities.

    Errors:
    - station_not_found — invalid station_id; call tempest_get_stations
    - auth_missing/auth_invalid/auth_forbidden — token not set, rejected,
      or lacking access; see the error's hint
    - rate_limited, upstream_unavailable (temporary; retry, honoring
      retry_after_ms when present)
    - Catalog: tempest_get_capabilities / tempest://capabilities
      (error_codes, error_channel); hint, when present, carries repair
      guidance

    Scope: the user's own WeatherFlow Tempest station(s) only — not a global
    or arbitrary-location weather service.
    """

    async def _work() -> ToolResult:
        fetched = await _get_station_details_data(station_id, ctx)
        result = fetched.data.model_dump(exclude=_STATION_EXCLUDE)
        return _validated("station", result, _meta_for(fetched))

    return await _dispatch(_work)


@mcp.tool(
    name="tempest_get_forecast",
    tags={"weather", "forecast"},
    annotations={
        "title": "Get Weather Forecast for a Station",
        "readOnlyHint": True,
        "openWorldHint": True,
    },
    output_schema=_FORECAST_SCHEMA,
)
async def get_forecast(
    station_id: Annotated[
        int, Field(description="The ID of the station to get forecast for", gt=0)
    ],
    hours: Annotated[
        int | None,
        Field(
            default=None,
            description=(
                "Number of hourly forecasts to return. Omit for the default depth "
                "of 6. Independent of `detailed`, which changes field density only."
            ),
            ge=1,
            le=48,
        ),
    ] = None,
    days: Annotated[
        int | None,
        Field(
            default=None,
            description=(
                "Number of daily forecasts to return. Omit for the default depth "
                "of 2. Independent of `detailed`, which changes field density only."
            ),
            ge=1,
            le=10,
        ),
    ] = None,
    detailed: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "If true, return full field density (including null fields and "
                "station coordinates). Default is a condensed summary. Controls "
                "field density only — entry counts come from hours/days alone."
            ),
        ),
    ] = False,
    ctx: Context | None = None,
) -> ToolResult:
    """Get the weather forecast for a station — includes a current snapshot
    plus hourly and daily forecasts.

    Use when: user asks about future weather ("will it rain tomorrow", "this
    weekend", "10-day forecast", "next few hours").

    Don't use for: current-only questions when tempest_get_observation will do —
    this returns a much larger response. If you need both current AND
    future, this tool covers both in one call.

    Workflow: requires station_id from tempest_get_stations. Entry counts come
    from hours/days alone (default 6 hourly / 2 daily when omitted); detailed
    changes field density, not how many entries come back. `truncated` is true
    only when upstream supplied fewer entries than you explicitly requested;
    `truncation_hint` then states the shortfall. A plain call (no hours/days)
    is never reported as truncated.

    Output: current snapshot + hourly + daily forecasts in the station's
    configured units — read 'units' in the response.

    Errors:
    - station_not_found — invalid station_id; call tempest_get_stations
    - auth_missing/auth_invalid/auth_forbidden — token not set, rejected,
      or lacking access; see the error's hint
    - rate_limited, upstream_unavailable (temporary; retry, honoring
      retry_after_ms when present)
    - Catalog: tempest_get_capabilities / tempest://capabilities
      (error_codes, error_channel); hint, when present, carries repair
      guidance

    Scope: the user's own WeatherFlow Tempest station(s) only — not a global
    or arbitrary-location weather service.
    """

    async def _work() -> ToolResult:
        fetched = await _get_forecast_data(station_id, ctx)
        result = fetched.data.model_dump(exclude=_FORECAST_EXCLUDE, exclude_none=not detailed)

        all_hourly = result["forecast"]["hourly"]
        all_daily = result["forecast"]["daily"]

        # Entry counts depend on hours/days ONLY — never on `detailed`, which
        # controls field density alone (exclude_none above, metadata pops
        # below). Omitting an axis means the default depth (6 hourly / 2
        # daily) in both modes.
        #
        # `detailed` used to also mean "all available entries" when hours/days
        # were omitted, which made one boolean move row count 38x (6 -> 230
        # hourly on a live station, a ~76 KB response) while leaving field
        # density untouched. Worse, it returned more hourly entries than the
        # `hours` maximum the input schema publishes. Row count is now the
        # sole province of hours/days, whose schema bounds (<=48, <=10) cap
        # the response for every caller.
        result["forecast"]["hourly"] = all_hourly[: 6 if hours is None else hours]
        result["forecast"]["daily"] = all_daily[: 2 if days is None else days]
        if not detailed:
            for key in ("latitude", "longitude", "timezone_offset_minutes"):
                result.pop(key, None)

        returned_hours = len(result["forecast"]["hourly"])
        returned_days = len(result["forecast"]["daily"])

        # `truncated` is measured against what the agent EXPLICITLY requested.
        # An omitted axis (None) can never be truncated — the agent didn't ask
        # for a specific count. The only remaining cause is an upstream
        # shortfall: WeatherFlow supplied fewer entries than requested.
        truncated = (hours is not None and returned_hours < hours) or (
            days is not None and returned_days < days
        )

        # returned_* are always factual; requested_* echo only what the agent
        # explicitly passed (omitted when None), so they never report a default
        # the agent didn't choose.
        result["truncated"] = truncated
        result["returned_hours"] = returned_hours
        result["returned_days"] = returned_days
        if hours is not None:
            result["requested_hours"] = hours
        else:
            result.pop("requested_hours", None)
        if days is not None:
            result["requested_days"] = days
        else:
            result.pop("requested_days", None)

        # Factual shortfall note, not a repair — the data does not exist
        # upstream, so there is no parameter change that recovers it.
        if truncated:
            shortfalls = []
            if hours is not None and returned_hours < hours:
                shortfalls.append(
                    f"upstream returned only {returned_hours} hourly entries "
                    f"for requested_hours={hours}"
                )
            if days is not None and returned_days < days:
                shortfalls.append(
                    f"upstream returned only {returned_days} daily entries "
                    f"for requested_days={days}"
                )
            result["truncation_hint"] = "; ".join(shortfalls)
        else:
            result.pop("truncation_hint", None)

        return _validated("forecast", result, _meta_for(fetched))

    return await _dispatch(_work)


@mcp.tool(
    name="tempest_get_observation",
    tags={"weather", "observations"},
    annotations={
        "title": "Get Current Weather Observations for a Station",
        "readOnlyHint": True,
        "openWorldHint": True,
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
) -> ToolResult:
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
    - station_not_found — invalid station_id; call tempest_get_stations
    - auth_missing/auth_invalid/auth_forbidden — token not set, rejected,
      or lacking access; see the error's hint
    - rate_limited, upstream_unavailable (temporary; retry, honoring
      retry_after_ms when present)
    - Catalog: tempest_get_capabilities / tempest://capabilities
      (error_codes, error_channel); hint, when present, carries repair
      guidance

    Scope: the user's own WeatherFlow Tempest station(s) only — not a global
    or arbitrary-location weather service.
    """

    async def _work() -> ToolResult:
        fetched = await _get_observation_data(station_id, ctx)

        if detailed:
            result = fetched.data.model_dump(exclude=_OBSERVATION_EXCLUDE)
        else:
            result = fetched.data.model_dump(exclude=_OBSERVATION_EXCLUDE, exclude_none=True)
            for obs in result["obs"]:
                for field_name in _OBSERVATION_SUMMARY_FIELDS:
                    obs.pop(field_name, None)
            for key in ("latitude", "longitude", "elevation", "is_public"):
                result.pop(key, None)

        return _validated("observation", result, _meta_for(fetched))

    return await _dispatch(_work)


@mcp.tool(
    name="tempest_get_capabilities",
    tags={"discovery"},
    annotations={
        "title": "Get Server Capabilities",
        "readOnlyHint": True,
        "openWorldHint": False,
    },
    output_schema=_CAPABILITIES_OUTPUT_SCHEMA,
)
async def get_capabilities() -> ToolResult:
    """Describe this server: scope, negative scope, tools, error codes,
    caching/latency behavior, and the capability fingerprint.

    Use when: you need the structured surface summary and your client does
    not expose MCP resources — this mirrors the tempest://capabilities
    resource exactly. Also useful to detect surface changes cheaply: compare
    `fingerprint` against a cached value instead of re-reading every tool.

    Don't use for: weather or station data (-> tempest_get_stations,
    tempest_get_observation, tempest_get_forecast).

    Output: static capability summary. Requires no API token and makes no
    upstream call.

    Errors:
    - invalid_argument — an unknown argument was passed (this tool takes none);
      omit it and retry
    - internal_error — server bug; report at
      https://github.com/briandconnelly/mcp-server-tempest/issues

    Scope: describes this server only — read-only access to the user's own
    WeatherFlow Tempest station(s), not a global or arbitrary-location
    weather service.
    """

    async def _work() -> ToolResult:
        return _validated(
            "capabilities",
            _build_capabilities(),
            {
                _META_KEY: {
                    "fingerprint": _FINGERPRINT,
                    "fingerprint_contract_version": _FINGERPRINT_CONTRACT_VERSION,
                }
            },
        )

    return await _dispatch(_work)


# Computed after every tool above is registered: the fingerprint derives tool
# names and input schemas from the live registry (see _compute_fingerprint).
# Tool bodies and the capabilities resource only read this at request time,
# so the late assignment is safe.
_FINGERPRINT = _compute_fingerprint()


if __name__ == "__main__":
    mcp.run()
