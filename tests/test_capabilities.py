"""Tests for the tempest://capabilities resource and surface fingerprint."""

import json
import os
from importlib.metadata import version
from unittest.mock import patch

import fastmcp
import pytest


@pytest.fixture(autouse=True)
def _set_token():
    with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "test-token"}):
        yield


async def test_capabilities_resource_shape():
    from mcp_server_tempest.server import mcp

    async with fastmcp.Client(mcp) as c:
        result = await c.read_resource("tempest://capabilities")
    payload = json.loads(result[0].text)

    assert payload["version"] == version("mcp-server-tempest")
    assert payload["fingerprint"].startswith("sha256:")
    assert payload["transport"] == "stdio"
    assert any("global" in s.lower() for s in payload["not_in_scope"])
    names = {t["name"] for t in payload["tools"]}
    assert names == {
        "tempest_get_stations",
        "tempest_get_station_details",
        "tempest_get_observation",
        "tempest_get_forecast",
        "tempest_get_capabilities",
    }
    assert "invalid_argument" in payload["error_codes"]
    assert "station_not_found" in payload["error_codes"]
    assert "RFC3339" in payload["timestamps"]
    assert "fingerprint_covers" in payload
    # F5: the error envelope is documented so agents know to branch on `code`.
    assert "code" in payload["error_channel"]
    assert "isError" in payload["error_channel"]
    # F1: latency / timeout behavior is declared.
    assert "timeout" in payload["latency"].lower()


def test_capability_contract_is_fingerprinted():
    """A1: changing the capability-summary prose must move the fingerprint, so
    a cached client can detect the change without re-walking the surface."""
    from mcp_server_tempest import server as s

    baseline = s._compute_fingerprint()
    mutated = {**s._CAPABILITY_CONTRACT, "scope": "something different"}
    with patch.object(s, "_CAPABILITY_CONTRACT", mutated):
        assert s._compute_fingerprint() != baseline


def test_input_schema_change_moves_fingerprint():
    """An input-contract change (new constraint, renamed parameter, changed
    description) must move the fingerprint without requiring a version bump."""
    from mcp_server_tempest import server as s

    baseline = s._compute_fingerprint()
    mutated = s._registered_input_schemas()
    mutated["tempest_get_forecast"]["properties"]["hours"]["description"] = "changed"
    with patch.object(s, "_registered_input_schemas", return_value=mutated):
        assert s._compute_fingerprint() != baseline


def test_annotation_change_moves_fingerprint():
    """F4: a tool-annotation flip (e.g. openWorldHint) must move the fingerprint
    so a cached client can detect the changed interaction boundary without
    re-walking the surface."""
    from mcp_server_tempest import server as s

    baseline = s._compute_fingerprint()
    mutated = s._registered_annotations()
    current = mutated["tempest_get_capabilities"] or {}
    mutated["tempest_get_capabilities"] = {**current, "openWorldHint": True}
    with patch.object(s, "_registered_annotations", return_value=mutated):
        assert s._compute_fingerprint() != baseline


async def test_fingerprinted_annotations_match_list_tools():
    """_registered_annotations reads FastMCP's private local registry; this
    guard compares it against the public (async) list_tools surface so a
    FastMCP upgrade that changes annotation serialization fails loudly here
    instead of silently fingerprinting the wrong contract."""
    from mcp_server_tempest import server as s

    hashed = s._registered_annotations()
    async with fastmcp.Client(s.mcp) as c:
        tools = await c.list_tools()
    live = {
        t.name: (
            t.annotations.model_dump(exclude_none=True, mode="json") if t.annotations else None
        )
        for t in tools
    }
    assert hashed == live


async def test_fingerprinted_input_schemas_match_list_tools():
    """_registered_input_schemas reads FastMCP's private local registry; this
    guard compares it against the public (async) list_tools surface so a
    FastMCP upgrade that moves the registry fails loudly here instead of
    silently fingerprinting the wrong contract."""
    from mcp_server_tempest import server as s

    hashed = s._registered_input_schemas()
    async with fastmcp.Client(s.mcp) as c:
        live = {t.name: t.inputSchema for t in await c.list_tools()}
    assert hashed == live


def test_fingerprint_is_deterministic_across_reload():
    """Verify the fingerprint value is stable across fresh imports.

    Uses a subprocess so that importlib.reload does not contaminate the shared
    module state that other test modules depend on (e.g. `cache`, `mcp`).
    """
    import subprocess
    import sys

    code = (
        "import os; os.environ.setdefault('WEATHERFLOW_API_TOKEN', 'test-token'); "
        "import mcp_server_tempest.server as s; fp1 = s._FINGERPRINT; "
        "import importlib; importlib.reload(s); fp2 = s._FINGERPRINT; "
        "assert fp2 == fp1, f'mismatch: {fp1!r} != {fp2!r}'; "
        "assert fp2.startswith('sha256:'); "
        "print(fp2)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith("sha256:")
