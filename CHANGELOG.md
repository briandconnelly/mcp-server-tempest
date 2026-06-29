# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Security hardening from the agent-friendliness review (two-model panel,
Claude + Codex). PR implemented with Claude and reviewed by Codex.

### Security

- `invalid_argument` errors no longer reflect untrusted input values back to
  the caller, closing a secret-leak path where an agent passing a credential
  as an unknown argument (e.g. `{"api_token": "sk-..."}`) would have it echoed
  into model context, transcripts, or client logs (#57). Unknown-field
  (`extra_forbidden`) values and any string input are dropped (all tool inputs
  are numeric/bool, so a string is never legitimate); only numeric/bool values
  with genuine repair signal (e.g. `station_id=-5`) are still reflected. As
  defense-in-depth, error values on sensitively-named fields are redacted.
- Disk cache directory and files are now created with owner-only permissions
  (`0700`/`0600`) and written atomically (temp file + `os.replace`), so cached
  station coordinates and Wi-Fi SSIDs are not readable by other local users on
  a multi-user host. Pre-existing loose permissions are migrated in place on
  startup (#61).

### Changed

- Tool annotations: `openWorldHint` is now `true` on the four WeatherFlow-backed
  tools (`tempest_get_stations`, `tempest_get_station_details`,
  `tempest_get_observation`, `tempest_get_forecast`), which reach an external
  service and return externally mutable data. It stays `false` on the static
  `tempest_get_capabilities`. This corrects the prior blanket `false`, which
  conflated a closed entity set with a closed interaction boundary (#58).
- The capability fingerprint now hashes each tool's `annotations`
  (`readOnlyHint`/`openWorldHint`/`title`), so a future annotation flip is
  visible to a cached client; previously only names, schemas, error codes,
  instructions, and the capability contract were covered. The
  `fingerprint_covers` text and the server-instructions wording were tightened
  to match what is actually hashed — tool descriptions/docstrings remain
  deliberately excluded (#60). This changes the fingerprint value once.

### Fixed

- `tempest_get_capabilities`'s documented error contract now lists
  `invalid_argument`, which it can return when an unknown argument is passed
  (the middleware maps the resulting validation failure to `invalid_argument`);
  the docstring previously listed only `internal_error`. Documentation-only
  fix — no behavior or fingerprint change.

## [0.9.0] - 2026-06-09

Agent-friendliness remediations from an MCP contract audit of the 0.8.0
surface (no Critical/Major findings; this addresses the remaining Minor/Nit
items). Plan reviewed with Codex; PR reviewed by Codex and GitHub Copilot.

### Breaking

- Tool-result `_meta` is now namespaced: the flat `cache`, `fingerprint`, and
  `ts_retrieved` keys moved under `_meta["net.bconnelly.tempest/fetch"]`.
  MCP reserves unprefixed `_meta` names for the protocol; there is no
  deprecation shim.
- `tempest_get_forecast` honors explicit `hours`/`days` as given in both
  modes; the 6 hourly / 2 daily summary caps apply only when an axis is
  omitted. Explicit requests beyond 6/2 in summary mode now return what was
  asked for instead of clipping. `detailed` is purely a field-density toggle,
  and `truncation_hint` is a factual upstream-shortfall note (there is no
  repair — the missing entries do not exist upstream).
- `fastmcp` dependency narrowed from `>=3.1` to `>=3.4,<4`: the fingerprint
  now reads FastMCP's tool registry, so an unbounded range could let a
  future major break import.

### Added

- `tempest_get_capabilities` tool mirroring the `tempest://capabilities`
  resource, for clients that surface MCP resources poorly. Requires no API
  token and makes no upstream call; its output schema is deliberately
  permissive (`additionalProperties: true`) so additive summary fields are
  never breaking.

### Changed

- The capability fingerprint now covers tool input schemas, derived from the
  live FastMCP registry exactly as clients see them (dialect-stamped). The
  "input-schema changes are reflected only via a version bump" carve-out is
  gone from `fingerprint_covers`. A guard test compares the registry read
  against public `list_tools()` so a FastMCP upgrade fails loudly.
- Tool annotations: `openWorldHint` is now `false` on every tool (one fixed
  upstream, closed entity set — network I/O alone is not open-world);
  `idempotentHint` is dropped (the MCP spec scopes it to non-read-only
  tools).
- Capability prose and instructions now state cache scope per tool and name
  the namespaced `_meta` key.

### Fixed

- The local prek `ty` gate had started failing on `main` (TTLCache generic
  inference); the two module caches now carry explicit type parameters.

## [0.8.0] - 2026-06-06

Agent-friendliness hardening from a contract audit (no Critical/Major findings;
these address the Minor/Nit items and one latent resource bug).

### Breaking

- `tempest_get_forecast`: `hours` and `days` now default to `None` instead of
  `12`/`5`. Omitting them yields the default depth (6 hourly / 2 daily in
  summary mode; all available entries in detailed mode). A plain call is no
  longer reported as `truncated`. `truncated` is now true only when fewer
  entries are returned than you **explicitly** requested; `requested_hours` /
  `requested_days` are emitted only when you pass them; `returned_hours` /
  `returned_days` are always present. `truncation_hint` appears only when a
  summary cap clipped an explicit request.

### Fixed

- Upstream WeatherFlow calls now run with an explicit 15s total timeout and a
  session the server owns and closes, fixing an aiohttp `ClientSession` leak on
  every uncached call (weatherflow4py never closed its own session). Timeouts
  and transport failures map to the retryable `upstream_unavailable` error.
- Progress and log notifications (`ctx.report_progress` / `ctx.info`) are now
  best-effort: a notification send failure can no longer turn a successful
  fetch into an `internal_error`.

### Added

- `error_channel` and `latency` fields in `tempest://capabilities`, documenting
  the JSON error envelope (branch on `code`, not `message`) and the per-call
  timeout behavior.

### Changed

- The capability fingerprint now covers the full `tempest://capabilities`
  contract (scope, tool purposes, error channel, latency), so a change to that
  prose moves the fingerprint a cached client can diff against.

### Removed

- Unreachable `/health` HTTP route (the server runs over stdio only).

## [0.7.0] - 2026-05-20

### Breaking

- All four tools are now published under `tempest_`-prefixed wire names:
  `tempest_get_stations`, `tempest_get_station_details`,
  `tempest_get_observation`, `tempest_get_forecast`. Clients must update
  any hardcoded tool-call names; the old unprefixed names are gone.

### Added

- `invalid_argument` structured error code for malformed tool arguments,
  raised by a contract middleware before the tool body runs. Clients receive
  the same flat JSON payload as all other errors, with `field` and `value`
  populated where applicable.
- `tempest://capabilities` discovery resource: a machine-readable summary of
  available tools, error codes, surface fingerprint, and server version.
  Agents can fetch this once to orient themselves without loading individual
  tool schemas.
- Surface fingerprint derived from the installed package version, exposed in
  the capabilities resource and in every tool result's `_meta.fingerprint`.
  Agents can detect server upgrades by comparing fingerprints across calls.
- Native `_meta` block on every tool result carrying `cache` state,
  `ts_retrieved` (RFC 3339 UTC timestamp of the underlying data fetch), and
  `fingerprint`. Clients that ignore `_meta` are unaffected.
- JSON Schema `$schema` dialect URI declared on all tool input and output
  schemas (`https://json-schema.org/draft/2020-12/schema`).

### Changed

- Concise (default) observation and forecast responses now omit null-valued
  optional fields to save tokens. Pass `detailed=True` to restore full
  fidelity with all fields present regardless of value.

## [0.6.0] - 2026-05-09

### Added

- Structured truncation fields on `ForecastResponse`: `truncated`,
  `requested_hours`, `requested_days`, `returned_hours`, `returned_days`,
  `truncation_hint`. Agents detect clipping without parsing prose; honest
  under both summary-cap and upstream-shortfall paths.
- Each tool docstring lists its structured `code` values, with per-tool
  subsets matching the call paths in `rest.py` (`get_stations` correctly
  excludes `station_not_found`).
- `SERVER SURFACE: mcp-server-tempest@<version>` line in the
  `instructions` block — a lightweight capability fingerprint per §9 of
  the agent-friendliness checklist. Read from package metadata at import
  time so it stays in sync with `pyproject.toml`.

### Changed

- Server `name` tightened from `"WeatherFlow Tempest API Server"` to
  `"WeatherFlow Tempest"` (drops the generic suffix).
- All published tool `outputSchema` definitions set
  `additionalProperties: false` recursively. Runtime ingest models stay
  permissive (`extra="ignore"`), so upstream WeatherFlow additions are
  silently dropped on parse rather than raising. Strict-mode clients
  should treat this as a tightening of the already-stable contract.
- Compressed agent-facing context for token efficiency: `instructions`
  block (NOTES, AMBIENT STATE, SERVER SURFACE), `get_stations` /
  `get_station_details` / `get_forecast` docstrings, and `hours` /
  `days` / `detailed` field descriptions. All required content
  (env-var names, cache path, transport, fingerprint format, error
  codes) preserved.
- Auth-code remediations in tool docstrings split per code
  (`auth_missing` / `auth_invalid` / `auth_forbidden`) instead of one
  inaccurate shared hint. `internal_error` bullets carry the actual
  issues URL.

## [0.5.0] - 2026-05-03

### Breaking

- All tool errors now return a structured JSON payload as the `ToolError`
  message (i.e. in `content[0].text` on the wire). The payload is a flat
  top-level object with stable fields:
  - `code` (string enum): one of `auth_missing`, `auth_invalid`,
    `auth_forbidden`, `station_not_found`, `rate_limited`,
    `upstream_unavailable`, `upstream_invalid_response`, `internal_error`.
  - `message` (string): human-readable summary; may change between versions.
  - `temporary` (bool): `true` for `rate_limited` and `upstream_unavailable`.
  - `request_id` (string): 16-hex-char per-call correlation id.
  - Optional: `hint`, `field`, `value`, `next` (e.g. `{"tool": "get_stations"}`),
    `retry_after_ms`, `details`.

  Clients parsing the previous prose `"Request failed: ..."` form must update
  to `JSON.parse(error.text)`. Clients MUST treat unknown top-level keys and
  unknown `code` values as opaque to remain forward-compatible.
- Removed the `mask_error_details=True` server config option (was a no-op
  because every tool already wrapped exceptions into a `FastMCPError`
  subclass, which the framework's masking explicitly skips).

### Added

- Distinct credential failure modes: `auth_missing` (env var unset),
  `auth_invalid` (upstream 401), `auth_forbidden` (upstream 403). Previously
  collapsed into one prose message.
- `request_id` is logged with every error and echoed in `internal_error`'s
  `hint` so users can correlate failures with server logs.

### Changed

- Server `instructions` now declares the ambient-state surface (cache env
  vars, disk cache path) and names the transport (stdio). Adds AMBIENT
  STATE, SETUP, and TRANSPORT sections; the previous trailing "Setup:"
  line is replaced by the new SETUP section. Closes audit F4 and F7.
- README: documented `WEATHERFLOW_DISK_CACHE_TTL` and the disk cache
  directory; added Caching & data freshness and Transport subsections.

## [0.4.0] - 2026-05-02

### Breaking

- Renamed tool `get_station_id` to `get_station_details`. Update any client
  code or prompts that called the old name.
- Removed `use_cache` parameter from `get_stations`, `get_station_details`,
  `get_observation`, and `get_forecast`. Caching follows
  `WEATHERFLOW_CACHE_TTL` only.
- Removed `clear_cache` tool. Restart the server or wait for the TTL to
  evict entries.
- Removed `weather://tempest/...` resources. Use the equivalent tools
  (`get_stations`, `get_station_details`, `get_observation`,
  `get_forecast`).

### Changed

- Rewrote the server `instructions` block and per-tool descriptions for
  clearer agent discovery and tool selection. Behavior is unchanged.

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
