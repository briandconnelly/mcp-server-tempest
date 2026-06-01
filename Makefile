.PHONY: manifest mcpb test lint

# Regenerate the MCPB manifest from pyproject.toml + the server's capabilities.
manifest:
	uv run python scripts/gen_manifest.py

# Version read from the manifest (the source of truth that is packed).
MCPB_VERSION := $(shell python3 -c 'import json; print(json.load(open("manifest.json"))["version"])')

# Build the installable .mcpb bundle (requires the mcpb CLI:
#   npm install -g @anthropic-ai/mcpb   — or use `npx @anthropic-ai/mcpb`).
mcpb: manifest
	mcpb validate manifest.json
	mkdir -p dist
	mcpb pack . dist/mcp-server-tempest-$(MCPB_VERSION).mcpb

test:
	uv run pytest

lint:
	uv run ruff check src/ tests/ scripts/
	uv run ruff format --check src/ tests/ scripts/
