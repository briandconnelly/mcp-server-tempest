"""Protocol-era parity: the server targets the sessionless 2026-07-28 revision
but must keep working for handshake-era clients on 2025-11-25.

`fastmcp.Client` negotiates the modern era by default, so the rest of the
suite already exercises 2026-07-28. Each test here runs against both eras so a
regression that only shows up on the handshake path fails loudly.
"""

import json
import os
from unittest.mock import AsyncMock, patch

import fastmcp
import pytest

import mcp_server_tempest.server as server_module
from mcp_server_tempest.middleware import JSON_SCHEMA_DIALECT
from mcp_server_tempest.server import cache, mcp

from .test_server import (
    SAMPLE_FORECAST_DATA,
    SAMPLE_OBSERVATION_DATA,
    SAMPLE_SINGLE_STATION_DATA,
    SAMPLE_STATION_DATA,
)

ERAS = [
    pytest.param("auto", "2026-07-28", id="sessionless-2026-07-28"),
    pytest.param("legacy", "2025-11-25", id="handshake-2025-11-25"),
]
MODES = [pytest.param(p.values[0], id=p.id) for p in ERAS]

TOOL_CALLS = [
    ("tempest_get_stations", {}),
    ("tempest_get_station_details", {"station_id": 12345}),
    ("tempest_get_observation", {"station_id": 12345}),
    ("tempest_get_forecast", {"station_id": 12345}),
    ("tempest_get_capabilities", {}),
]


@pytest.fixture(autouse=True)
def _isolated_upstream():
    """Stub every WeatherFlow call and keep caches out of the picture."""
    cache.clear()
    server_module._fetch_times.clear()
    with (
        patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "test-token"}),
        patch.object(server_module, "_get_disk_cache", return_value=None),
        patch.object(server_module, "disk_cache", None),
        patch.object(
            server_module, "api_get_stations", AsyncMock(return_value=SAMPLE_STATION_DATA)
        ),
        patch.object(
            server_module,
            "api_get_station_id",
            AsyncMock(return_value=SAMPLE_SINGLE_STATION_DATA),
        ),
        patch.object(
            server_module, "api_get_observation", AsyncMock(return_value=SAMPLE_OBSERVATION_DATA)
        ),
        patch.object(
            server_module, "api_get_forecast", AsyncMock(return_value=SAMPLE_FORECAST_DATA)
        ),
    ):
        yield
    cache.clear()
    server_module._fetch_times.clear()


@pytest.mark.parametrize(("mode", "revision"), ERAS)
async def test_negotiates_expected_revision(mode, revision):
    async with fastmcp.Client(mcp, mode=mode) as c:
        assert c.protocol_version == revision


@pytest.mark.parametrize("mode", MODES)
async def test_tool_list_is_identical_across_eras(mode):
    async with fastmcp.Client(mcp, mode=mode) as c:
        tools = await c.list_tools()
    assert {t.name for t in tools} == {name for name, _ in TOOL_CALLS}
    for t in tools:
        assert t.input_schema.get("$schema") == JSON_SCHEMA_DIALECT, t.name
        assert (t.output_schema or {}).get("$schema") == JSON_SCHEMA_DIALECT, t.name
        assert t.annotations is not None and t.annotations.read_only_hint is True, t.name


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize(("tool", "args"), TOOL_CALLS, ids=[name for name, _ in TOOL_CALLS])
async def test_every_tool_succeeds(mode, tool, args):
    async with fastmcp.Client(mcp, mode=mode) as c:
        r = await c.call_tool(tool, args)
    assert not r.is_error
    assert r.structured_content


@pytest.mark.parametrize("mode", MODES)
async def test_invalid_argument_is_structured(mode):
    async with fastmcp.Client(mcp, mode=mode) as c:
        r = await c.call_tool_mcp("tempest_get_observation", {"station_id": -5})
    assert r.is_error is True
    payload = json.loads(r.content[0].text)
    assert payload["code"] == "invalid_argument"
    assert payload["field"] == "station_id"
    assert r.structured_content == payload
