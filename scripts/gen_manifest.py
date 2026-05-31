#!/usr/bin/env python
"""Generate ``manifest.json`` (the MCPB bundle manifest) from a single source
of truth.

Identity (name/version/description/author) comes from ``pyproject.toml``; the
tool list is derived from the server's own capabilities so the manifest cannot
drift from what the server actually exposes. ``tests/test_manifest.py`` asserts
the committed ``manifest.json`` matches this generator's output, so regenerate
and commit whenever the version or tool surface changes.

Usage:
    uv run python scripts/gen_manifest.py            # write manifest.json
    uv run python scripts/gen_manifest.py --check     # exit 1 if stale
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

from mcp_server_tempest.server import _build_capabilities

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
MANIFEST = REPO_ROOT / "manifest.json"

REPO_URL = "https://github.com/briandconnelly/mcp-server-tempest"
KEYWORDS = ["weather", "tempest", "weatherflow", "mcp"]


def _tools() -> list[dict[str, str]]:
    """Manifest ``tools`` entries, derived from the server's capabilities so the
    name/description pairs stay in lockstep with the live server."""
    return [
        {"name": tool["name"], "description": tool["purpose"]}
        for tool in _build_capabilities()["tools"]
    ]


def build_manifest() -> dict:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    author = project["authors"][0]

    return {
        "manifest_version": "0.4",
        "name": project["name"],
        "display_name": "WeatherFlow Tempest",
        "version": project["version"],
        "description": project["description"],
        "author": {"name": author["name"], "email": author["email"]},
        "repository": {"type": "git", "url": REPO_URL},
        "homepage": REPO_URL,
        "documentation": "https://weatherflow.github.io/Tempest/api/",
        "support": f"{REPO_URL}/issues",
        "license": "MIT",
        "keywords": KEYWORDS,
        "server": {
            "type": "uv",
            "entry_point": "src/mcp_server_tempest/__main__.py",
            "mcp_config": {
                "command": "uv",
                "args": [
                    "run",
                    "--directory",
                    "${__dirname}",
                    "--frozen",
                    "--no-dev",
                    "python",
                    "-m",
                    "mcp_server_tempest",
                ],
                "env": {
                    "WEATHERFLOW_API_TOKEN": "${user_config.api_token}",
                    "WEATHERFLOW_CACHE_TTL": "${user_config.cache_ttl}",
                    "WEATHERFLOW_CACHE_SIZE": "${user_config.cache_size}",
                    "WEATHERFLOW_DISK_CACHE_TTL": "${user_config.disk_cache_ttl}",
                },
            },
        },
        "compatibility": {
            "platforms": ["darwin", "linux", "win32"],
            "runtimes": {"python": ">=3.13"},
        },
        "user_config": {
            "api_token": {
                "type": "string",
                "title": "WeatherFlow API Token",
                "description": "Personal token from https://tempestwx.com/settings/tokens",
                "sensitive": True,
                "required": True,
            },
            "cache_ttl": {
                "type": "number",
                "title": "In-memory cache TTL (seconds)",
                "description": "How long tool responses are cached in memory.",
                "default": 300,
                "required": False,
            },
            "cache_size": {
                "type": "number",
                "title": "Max in-memory cache entries",
                "description": "Maximum number of cached responses held in memory.",
                "default": 100,
                "required": False,
            },
            "disk_cache_ttl": {
                "type": "number",
                "title": "Disk cache TTL (seconds)",
                "description": "How long station/details responses persist on disk.",
                "default": 86400,
                "required": False,
            },
        },
        "tools": _tools(),
    }


def render(manifest: dict) -> str:
    """Deterministic JSON rendering used for both writing and drift comparison."""
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if manifest.json is missing or stale (do not write).",
    )
    args = parser.parse_args()

    rendered = render(build_manifest())

    if args.check:
        current = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
        if current != rendered:
            print("manifest.json is out of date; run: uv run python scripts/gen_manifest.py")
            return 1
        print("manifest.json is up to date.")
        return 0

    MANIFEST.write_text(rendered, encoding="utf-8")
    print(f"Wrote {MANIFEST.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
