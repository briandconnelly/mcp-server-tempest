"""Guards for the Claude Code / Codex plugin packaged at the repository root.

The plugin (``.claude-plugin/``, ``.codex-plugin/``, ``.mcp.json``, ``skills/``)
ships the MCP server pinned to a PyPI release plus the skills that drive it.
These tests keep its version pins in lockstep with ``pyproject.toml`` and keep
the skills from naming tools the server does not expose.
"""

import json
import os
import re
import tomllib
from pathlib import Path
from unittest.mock import patch

import fastmcp
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
VERSION = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
    "version"
]
SKILL_FILES = sorted(SKILLS_DIR.glob("*/SKILL.md"))

# Tool names as the plugin exposes them to Claude Code (allowed-tools).
_PLUGIN_TOOL = re.compile(r"mcp__plugin_tempest_mcp-server-tempest__(\w+)")
_TOOL_MENTION = re.compile(r"\btempest_get_\w+")


@pytest.fixture(autouse=True)
def _set_token():
    with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "test-token"}):
        yield


async def _registered_tools() -> set[str]:
    from mcp_server_tempest.server import mcp

    async with fastmcp.Client(mcp) as client:
        return {t.name for t in await client.list_tools()}


@pytest.mark.parametrize("manifest", [".claude-plugin/plugin.json", ".codex-plugin/plugin.json"])
def test_plugin_version_matches_pyproject(manifest):
    """Hosts key an installed plugin by this version; bump it with pyproject."""
    data = json.loads((REPO_ROOT / manifest).read_text(encoding="utf-8"))
    assert data["version"] == VERSION


def test_mcp_json_pins_the_release():
    """The plugin runs the server from PyPI, pinned to this tree's version."""
    config = json.loads((REPO_ROOT / ".mcp.json").read_text(encoding="utf-8"))
    args = config["mcpServers"]["mcp-server-tempest"]["args"]
    assert f"mcp-server-tempest=={VERSION}" in args


def test_skills_present():
    assert {p.parent.name for p in SKILL_FILES} == {"estimate-cloudiness", "weather-report"}


@pytest.mark.parametrize("skill", SKILL_FILES, ids=lambda p: p.parent.name)
def test_skill_name_matches_directory(skill):
    text = skill.read_text(encoding="utf-8")
    match = re.search(r"^name:\s*(\S+)\s*$", text, re.MULTILINE)
    assert match is not None, f"{skill} has no name in its frontmatter"
    assert match.group(1) == skill.parent.name


@pytest.mark.parametrize("skill", SKILL_FILES, ids=lambda p: p.parent.name)
def test_skill_openai_yaml_interface(skill):
    """agents/openai.yaml drives the skill's chip in Codex / the ChatGPT app.
    Limits follow openai/skills' interface schema (short_description 25-64
    characters; default_prompt invokes the skill as `$<name>`)."""
    path = skill.parent / "agents" / "openai.yaml"
    assert path.exists(), f"{path} missing"
    interface = yaml.safe_load(path.read_text(encoding="utf-8"))["interface"]
    assert interface["display_name"]
    assert 25 <= len(interface["short_description"]) <= 64
    assert f"${skill.parent.name}" in interface["default_prompt"]
    for text in interface.values():
        assert "<" not in text and ">" not in text


@pytest.mark.parametrize("skill", SKILL_FILES, ids=lambda p: p.parent.name)
async def test_skill_names_only_real_tools(skill):
    """A renamed or removed tool must not leave a skill calling it."""
    text = skill.read_text(encoding="utf-8")
    named = set(_PLUGIN_TOOL.findall(text)) | set(_TOOL_MENTION.findall(text))
    assert named, f"{skill} names no tools; is the pattern stale?"
    assert named <= await _registered_tools()
