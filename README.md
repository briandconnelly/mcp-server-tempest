# WeatherFlow Tempest MCP Server

A Model Context Protocol (MCP) server that gives AI assistants read-only access to **your own**
WeatherFlow Tempest weather station(s): current observations, forecasts, and station metadata.

It is not a general weather service. It does not cover:

- locations away from your station, or global/regional weather (use a public weather API)
- air quality, pollen, or smoke
- severe-weather alerts, radar, or watches/warnings
- historical archives beyond what the live Tempest API returns


## 🌤️ Features

- **Current conditions** from your station: temperature, humidity, pressure, wind, rain,
  solar radiation, UV, and lightning
- **Forecasts**: hourly (up to 48 h) and daily (up to 10 days), plus a current snapshot
- **Station inventory**: your stations, their locations, devices, and sensor capabilities
- **Caching** in memory and on disk, with a `refresh` option for the latest reading
- **Structured results and errors** for agents: typed output schemas, explicit units,
  RFC3339 timestamps, and error responses that include a ready-to-run corrected call


## 🚀 Quick Start

### Prerequisites

- Python 3.13 or higher
- WeatherFlow API token (get one at [tempestwx.com/settings/tokens](https://tempestwx.com/settings/tokens))

### Installation

While each client has its own way of specifying, you'll generally use the following values:

| Field | Value |
|-------|-------|
| **Command** | `uvx` |
| **Arguments** | `mcp-server-tempest` |
| **Environment** | `WEATHERFLOW_API_TOKEN` = `<YOUR TOKEN>` |


### Development Version

If you'd like to use the latest and greatest, the server can be pulled straight from GitHub.
Just add an additional `--from` argument:


| Field | Value |
|-------|-------|
| **Command** | `uvx` |
| **Arguments** | `--from`, `git+https://github.com/briandconnelly/mcp-server-tempest`, `mcp-server-tempest` |
| **Environment** | `WEATHERFLOW_API_TOKEN` = `<YOUR TOKEN>` |


### Install as a Claude Code or Codex plugin

The `tempest` plugin bundles the server with two skills — `weather-report`
(current conditions, forecasts, and weather-based decisions) and
`estimate-cloudiness` (sky condition from solar radiation). In Claude Code:

```
/plugin marketplace add briandconnelly/briandconnelly-plugins
/plugin install tempest@briandconnelly-plugins
```

Set `WEATHERFLOW_API_TOKEN` in your environment before starting the client.
The plugin's sources live in this repository (`.claude-plugin/`,
`.codex-plugin/`, `.mcp.json`, `skills/`).


### Install as a Desktop Extension (`.mcpb`)

For one-click installation in apps that support [MCP Bundles](https://github.com/modelcontextprotocol/mcpb/)
(e.g. Claude for macOS/Windows):

1. Download the `.mcpb` from the
   [latest release](https://github.com/briandconnelly/mcp-server-tempest/releases).
2. Open the file with your MCPB-capable client to launch the install dialog.
3. Paste your WeatherFlow API token when prompted (the cache settings are optional).
4. Make sure the extension is **enabled** (in Claude Desktop: Settings →
   Extensions). It is not turned on automatically until the required API token
   has been provided.

The bundle uses the MCPB `uv` runtime (`manifest_version` `0.4`), so the host
must ship a recent enough `uv`/MCPB runtime; it resolves dependencies on first
launch — no separate Python install is required.

> **Troubleshooting:** if the server fails to start because its install
> directory is read-only (uv cannot create a `.venv` next to the bundle), set
> the `UV_PROJECT_ENVIRONMENT` environment variable for the server to a writable
> path before launching.


## 📋 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `WEATHERFLOW_API_TOKEN` | Your WeatherFlow API token | - | ✅ Yes |
| `WEATHERFLOW_CACHE_TTL` | In-memory cache TTL in seconds | 300 | No |
| `WEATHERFLOW_CACHE_SIZE` | Maximum in-memory cache entries | 100 | No |
| `WEATHERFLOW_DISK_CACHE_TTL` | Disk cache TTL in seconds | 86400 | No |

### Caching & data freshness

The server caches responses in two layers:

- **In-memory** (`WEATHERFLOW_CACHE_TTL` / `WEATHERFLOW_CACHE_SIZE`): all four
  data tools (`tempest_get_capabilities` is static and uncached).
- **On disk** (`WEATHERFLOW_DISK_CACHE_TTL`, default 24h): `tempest_get_stations` and
  `tempest_get_station_details` only. Stored under
  `platformdirs.user_cache_dir("mcp-server-tempest")` in a per-token
  (hash-keyed) subdirectory.

To bypass the cache for current data, pass `refresh=true` to
`tempest_get_observation` or `tempest_get_forecast`. Station data has no
`refresh` argument: to clear it, restart the server (in-memory) or delete the
cache directory (disk). Every data result carries `retrieved_at`, the time the
server fetched it from WeatherFlow.

### Transport

stdio (the default for `uvx mcp-server-tempest` and the configuration above).


## 🛠️ Usage

### Tools

| Tool | Use it for | Arguments |
|------|-----------|-----------|
| `tempest_get_stations` | Listing your stations, their locations, and devices. Start here: station IDs can't be guessed. | none |
| `tempest_get_station_details` | One station's configuration and hardware, plus the sensor `capabilities` the station list omits | `station_id` |
| `tempest_get_observation` | Current conditions | `station_id`; `detailed` (default `false`: condensed); `refresh` (default `false`) |
| `tempest_get_forecast` | Hourly and daily forecast, plus a current snapshot | `station_id`; `hours` 1–48 (default 6); `days` 1–10 (default 2); `detailed`; `refresh` |
| `tempest_get_capabilities` | What the server does and doesn't do, its tools, error codes, and a fingerprint of its interface. Needs no API token. | none |

The same capability summary is available as the MCP resource `tempest://capabilities`.
It is the authoritative, machine-readable contract; the table above is a quick guide.

### Reading results

- **Units.** Observation values are always metric/SI and are described by the result's
  `units` object. Forecast values are described by the forecast's own `units`. The
  observation's `station_units` is the station owner's *display preference*, not the unit
  of the values: convert to it when presenting. Only observations carry `station_units`.
- **Times.** Raw fields such as `timestamp`, `time`, and `lightning_strike_last_epoch` are
  Unix seconds. Each has an RFC3339 UTC `*_at` twin: `observed_at` and
  `lightning_strike_last_at` on observations and the forecast's `current_conditions`,
  `sunrise_at`, `sunset_at`, and `day_start_at` on daily forecasts, and `starts_at` on
  hourly forecasts. Every data result carries `retrieved_at`, when it was fetched upstream.
  Hourly forecast entries include `local_day` and `local_hour` in the station's own timezone.
- **Errors** come back as a tool error whose structured content has a symbolic `code`
  (branch on it, not on `message`), `temporary` (plus `retry_after_ms` when true), and,
  when the server can build one, `repair`: a corrected call to make as-is. The full error
  contract is the `error_channel` field of the capability summary. Version 0.11.0 changed
  the error format (`next` became `repair`); see the [CHANGELOG](CHANGELOG.md).


## 🌟 Example questions

Once the server is configured, ask your assistant in plain language. Some examples, with the
tool it will typically use:

| You ask | Tool |
|---------|------|
| "What weather stations do I have?" / "What's my station's elevation?" | `tempest_get_stations` |
| "Is it raining at home right now?" / "How windy is it?" | `tempest_get_observation` |
| "Has there been any lightning nearby?" | `tempest_get_observation` |
| "Will it freeze tonight?" / "What's the forecast for the weekend?" | `tempest_get_forecast` |
| "Is it a good afternoon for a run?" | `tempest_get_forecast` |
| "What can my station measure?" / "What hardware does it have?" | `tempest_get_station_details` |
| "What can this weather server do?" | `tempest_get_capabilities` |

Building your own client instead? Any MCP client works; the tools return structured
results described by each tool's output schema. See, for example, the
[FastMCP client docs](https://gofastmcp.com/clients/client).


## 🤝 Contributing

Contributions are welcome. [AGENTS.md](AGENTS.md) is the guide for humans and AI agents
alike: environment setup with `uv`, how to run the tests and linters, branch and commit
conventions (conventional commits; signed commits on `main`), and how pull requests are
reviewed and merged. Release notes live in [CHANGELOG.md](CHANGELOG.md).

Please report security issues privately, as described in [SECURITY.md](SECURITY.md).


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [WeatherFlow](https://weatherflow.com/) for providing the Tempest weather station and API
- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP specification
- [FastMCP](https://github.com/PrefectHQ/fastmcp) for the MCP server framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/briandconnelly/mcp-server-tempest/issues)
- **Documentation**: [WeatherFlow API Docs](https://weatherflow.github.io/Tempest/api/)
- **Community**: [WeatherFlow Community](https://community.weatherflow.com/)
