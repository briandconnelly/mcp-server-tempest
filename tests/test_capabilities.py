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
    }
    assert "invalid_argument" in payload["error_codes"]
    assert "station_not_found" in payload["error_codes"]
    assert "RFC3339" in payload["timestamps"]
    assert "fingerprint_covers" in payload


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
