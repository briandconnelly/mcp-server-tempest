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


def _mutated_tool_records(server, tool, **overrides):
    """A copy of the wire tool records with one tool's fields overridden."""
    records = server._wire_tool_records()
    records[tool] = {**records[tool], **overrides}
    return records


def test_input_schema_change_moves_fingerprint():
    """An input-contract change (new constraint, renamed parameter, changed
    description) must move the fingerprint without requiring a version bump."""
    from mcp_server_tempest import server as s

    baseline = s._compute_fingerprint()
    records = s._wire_tool_records()
    records["tempest_get_forecast"]["inputSchema"]["properties"]["hours"]["description"] = "changed"
    with patch.object(s, "_wire_tool_records", return_value=records):
        assert s._compute_fingerprint() != baseline


def test_annotation_change_moves_fingerprint():
    """F4: a tool-annotation flip (e.g. openWorldHint) must move the fingerprint
    so a cached client can detect the changed interaction boundary without
    re-walking the surface."""
    from mcp_server_tempest import server as s

    baseline = s._compute_fingerprint()
    records = s._wire_tool_records()
    current = records["tempest_get_capabilities"].get("annotations") or {}
    # Toggle the current value so the mutation is always a real change, even if
    # the tool's default openWorldHint ever flips.
    mutated = _mutated_tool_records(
        s,
        "tempest_get_capabilities",
        annotations={**current, "openWorldHint": not current.get("openWorldHint", False)},
    )
    with patch.object(s, "_wire_tool_records", return_value=mutated):
        assert s._compute_fingerprint() != baseline


def test_tool_description_change_moves_fingerprint():
    """F7: tool descriptions are the primary input to tool selection, so a
    description-only edit must move the fingerprint.

    Contract version 1 excluded descriptions to avoid churn on prose polish.
    That mistook the fingerprint doing its job for a cost: a client caching the
    surface must be told when the document it selects tools from changes.
    """
    from mcp_server_tempest import server as s

    baseline = s._compute_fingerprint()
    mutated = _mutated_tool_records(
        s, "tempest_get_stations", description="Completely different selection guidance."
    )
    with patch.object(s, "_wire_tool_records", return_value=mutated):
        assert s._compute_fingerprint() != baseline


def test_tool_title_change_moves_fingerprint():
    """Titles steer human-facing pickers, so they are agent-visible surface too."""
    from mcp_server_tempest import server as s

    baseline = s._compute_fingerprint()
    mutated = _mutated_tool_records(s, "tempest_get_stations", title="Renamed In The Picker")
    with patch.object(s, "_wire_tool_records", return_value=mutated):
        assert s._compute_fingerprint() != baseline


@pytest.mark.parametrize("field", ["name", "description", "mimeType"])
def test_resource_record_change_moves_fingerprint(field):
    """F7: the resource catalog is agent-visible surface. Contract version 1
    hashed no resource record at all, so renaming or re-describing
    tempest://capabilities was invisible to a fingerprint-caching client."""
    from mcp_server_tempest import server as s

    baseline = s._compute_fingerprint()
    records = s._wire_resource_records()
    uri = "tempest://capabilities"
    records[uri] = {**records[uri], field: "changed"}
    with patch.object(s, "_wire_resource_records", return_value=records):
        assert s._compute_fingerprint() != baseline


async def test_fingerprinted_tool_records_match_list_tools():
    """_wire_tool_records reads FastMCP's private local registry; this guard
    compares it byte-for-byte against the public (async) list_tools surface, so
    a FastMCP upgrade that moves the registry or changes serialization fails
    loudly here instead of silently fingerprinting the wrong contract."""
    from mcp_server_tempest import server as s

    hashed = s._wire_tool_records()
    async with fastmcp.Client(s.mcp) as c:
        tools = await c.list_tools()
    live = {t.name: t.model_dump(exclude_none=True, mode="json", by_alias=True) for t in tools}
    assert hashed == live


async def test_fingerprinted_resource_records_match_list_resources():
    """Same guard for the resource catalog."""
    from mcp_server_tempest import server as s

    hashed = s._wire_resource_records()
    async with fastmcp.Client(s.mcp) as c:
        resources = await c.list_resources()
    live = {
        str(r.uri): r.model_dump(exclude_none=True, mode="json", by_alias=True) for r in resources
    }
    assert hashed == live


async def test_fingerprint_stable_across_list_tools():
    """The middleware stamps $schema onto live component dicts when a client
    calls tools/list. _wire_tool_records applies the same stamp, so the
    fingerprint must not shift after the first list call — otherwise the
    published _FINGERPRINT (computed at import) would disagree with a
    recomputation."""
    from mcp_server_tempest import server as s

    before = s._compute_fingerprint()
    async with fastmcp.Client(s.mcp) as c:
        await c.list_tools()
    assert s._compute_fingerprint() == before == s._FINGERPRINT


def test_missing_tool_description_is_refused():
    """`python -OO` strips docstrings, so tool descriptions vanish and the
    catalog becomes unselectable. Refuse rather than serve it, and never
    substitute a placeholder — absent descriptions are a genuinely different
    agent-visible surface."""
    from mcp_server_tempest import server as s

    stripped = _mutated_tool_records(s, "tempest_get_stations", description=None)
    del stripped["tempest_get_stations"]["description"]
    with pytest.raises(RuntimeError, match="missing descriptions"):
        s._require_tool_descriptions(stripped)

    # The real records pass.
    s._require_tool_descriptions(s._wire_tool_records())


def test_protocol_contract_is_published_and_fingerprinted():
    """The authored target is distinct from what a session negotiates, and the
    accepted set is read from the SDK so it cannot claim revisions the server
    would reject."""
    from mcp.server.session import SUPPORTED_PROTOCOL_VERSIONS

    from mcp_server_tempest import server as s

    protocol = s._build_capabilities()["protocol"]
    assert protocol["authored_target"] == "2025-11-25"
    assert protocol["accepted_revisions"] == sorted(SUPPORTED_PROTOCOL_VERSIONS)
    assert protocol["authored_target"] in protocol["accepted_revisions"]

    baseline = s._compute_fingerprint()
    with patch.object(s, "_MCP_PROTOCOL", {**s._MCP_PROTOCOL, "authored_target": "2024-11-05"}):
        assert s._compute_fingerprint() != baseline


def test_fingerprint_contract_version_is_published():
    """Clients need to tell 'the surface changed' from 'the surface is now
    measured differently'."""
    from mcp_server_tempest import server as s

    payload = s._build_capabilities()
    assert payload["fingerprint_contract_version"] == s._FINGERPRINT_CONTRACT_VERSION == 2
    assert "fingerprint_contract_version" in payload["fingerprint_covers"]


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
