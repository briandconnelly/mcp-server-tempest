# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-03-28

### Added

- Station cache pre-warming: on startup, the server loads station data from
  disk cache into the in-memory TTL cache, eliminating cold-start latency for
  the first tool call.
- `detailed` parameter on `get_forecast` and `get_observation` tools
  (default: `false`). Summary mode returns condensed responses to reduce LLM
  context usage; detailed mode returns the full response.
- `hours` and `days` parameters on `get_forecast` to control forecast depth
  (defaults: 12 hourly, 5 daily). In summary mode, these are capped at 6 and
  2 respectively.
- Typed `output_schema` on all tools via `_relaxed_schema()`, which generates
  JSON schemas from Pydantic models with only excluded fields marked optional.
  Clients see full field names, types, and descriptions while filtered
  responses pass FastMCP output validation.

### Changed

- Tools now return filtered dicts (via `model_dump(exclude=...)`) instead of
  full Pydantic model instances. Low-value fields are excluded to reduce
  response size:
  - **All tools**: icon identifiers (`icon`, `precip_icon`)
  - **Station tools**: internal IDs (`station_item_id`, `location_id`,
    `location_item_id`), share flags (`share_with_wf`, `share_with_wu`),
    capability metadata (`device_id`, `agl`, `show_precip_final`), timestamps
    (`created_epoch`, `last_modified_epoch`)
  - **Observation tools**: `outdoor_keys` always excluded; summary mode also
    drops derived fields (`heat_index`, `wind_chill`, `wet_bulb_temperature`,
    `delta_t`, `air_density`, `brightness`, and others)
  - **Forecast tools**: summary mode drops `latitude`, `longitude`,
    `timezone_offset_minutes`
- Resource functions remain unchanged (return full Pydantic models).
- Tool docstrings shortened for conciseness.
- `use_cache` parameter now has a Python-level default value on all tools.

## [0.3.0] - 2026-03-28

### Added

- Persistent disk cache for station metadata using JSON files, surviving server
  restarts. Station lookups now use a 3-tier strategy: in-memory TTL cache, disk
  cache (24h default TTL), then API. Forecasts and observations remain
  in-memory only.
- Disk cache is scoped per API token (via SHA-256 hash) to isolate data between
  accounts.
- `WEATHERFLOW_DISK_CACHE_TTL` environment variable to configure disk cache TTL
  (default: 86400 seconds / 24 hours).
- `platformdirs` dependency for OS-appropriate cache directory resolution.
- `AIR` and `SKY` variants to the `DeviceType` enum, matching the full set of
  WeatherFlow device types.
- Disk cache key sanitization to prevent path traversal.
- Validation for `WEATHERFLOW_CACHE_TTL` and `WEATHERFLOW_CACHE_SIZE` environment
  variables with warning and fallback to defaults on invalid values.
- Tests for disk cache, disk cache integration, exception passthrough, env var
  validation, and empty API response handling.

### Changed

- `clear_cache` tool now clears both in-memory and disk caches.
- `_get_api_token` is now synchronous (was unnecessarily async).
- Tools now re-raise `ToolError` directly instead of re-wrapping it, preserving
  the original error message.
- Exception chaining (`from e`) added throughout for better tracebacks.
- Disk cache serialization uses `model_dump(mode="json")` for safe handling of
  non-JSON-native types.
- Type annotations modernized to use `list[]` and `X | None` syntax (Python
  3.13+).

### Fixed

- `api_get_station_id` no longer crashes with `IndexError` on empty API
  responses; raises `ValueError` with a descriptive message instead.
- Module docstring referenced incorrect entry point (`python -m weatherflow_mcp`).

## [0.2.0] - 2026-03-28

### Added

- `__version__` attribute via `importlib.metadata`.
- Tool tags, progress reporting, lifespan hook, and health check endpoint
  using FastMCP 3.x features.
- `mask_error_details` and `on_duplicate="error"` server configuration.
- Dev dependencies: pytest, pytest-asyncio, pytest-cov, ruff.
- 61 tests across models, REST client, and server.
- GitHub Actions CI workflow (lint + test).
- Claude Code GitHub Actions workflows.

### Changed

- Upgraded `fastmcp` from 2.x to 3.1+.
- Fixed `idempotentHint` on read-only tools (was `False`, now `True`).
- Fixed resource return types and docstring errors.

### Fixed

- `TTLCache` `TypeError` when cache environment variables are set as strings
  (#1).
- README placeholder URL (`yourusername` -> `briandconnelly`).
- Removed unused imports and non-existent resource URI from instructions.

## [0.1.0] - 2025-07-22

### Added

- Initial release.
- MCP server for WeatherFlow Tempest weather station data.
- Tools: `get_stations`, `get_station_id`, `get_forecast`, `get_observation`,
  `clear_cache`.
- Resources for stations, forecasts, and observations.
- In-memory TTL cache with configurable size and TTL.
- Pydantic models for all API responses.
- Tool annotations and resource URIs.
- README and LICENSE.
