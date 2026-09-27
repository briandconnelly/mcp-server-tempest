"""Suite-wide test configuration."""

import fastmcp

# FastMCP 4 bridges the MCP SDK v1 camelCase attribute names (`isError`,
# `inputSchema`, ...) onto the SDK v2 snake_case models, warning once per name.
# The bridge is scheduled for removal, so turn it off here: any remaining
# camelCase read fails as an AttributeError now instead of when the shim goes.
# The setting is read on every access, so flipping it after import is enough.
fastmcp.settings.mcp_camelcase_compat = False
