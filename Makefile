.PHONY: manifest mcpb test lint

# Regenerate the MCPB manifest from pyproject.toml + the server's capabilities.
manifest:
	uv run python scripts/gen_manifest.py

# Build the installable .mcpb bundle (requires the mcpb CLI:
#   npm install -g @anthropic-ai/mcpb   — or use `npx @anthropic-ai/mcpb`).
mcpb: manifest
	mcpb validate manifest.json
	mkdir -p dist
	mcpb pack . dist/mcp-server-tempest.mcpb

test:
	uv run pytest

lint:
	uv run ruff check src/ tests/ scripts/
	uv run ruff format --check src/ tests/ scripts/
