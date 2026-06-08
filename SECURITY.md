# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities **privately** rather than opening a
public issue. Use GitHub's [private vulnerability
reporting](https://github.com/briandconnelly/mcp-server-tempest/security/advisories/new)
(the **Security** tab → *Report a vulnerability*).

Include enough detail to reproduce the issue (affected version, configuration,
and a minimal repro where possible). You can expect an initial acknowledgement
within a few days; please allow reasonable time for a fix before any public
disclosure.

## Supported versions

This project is pre-1.0 (`0.x`): only the latest released version receives
security fixes. Older `0.x` releases are not maintained.

## Scope

`mcp-server-tempest` is a read-only MCP server that exposes a user's own
WeatherFlow Tempest station data via the official WeatherFlow REST API. It
holds a single secret — the user's `WEATHERFLOW_API_TOKEN` — supplied through
the environment and never logged. Reports about token handling, the REST
client, caching, or the MCP tool surface are in scope. General WeatherFlow
service issues should go to WeatherFlow directly.
