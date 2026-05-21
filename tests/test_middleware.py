"""Wire-level tests for TempestContractMiddleware via fastmcp.Client."""

import json
import os
from unittest.mock import patch

import fastmcp
import pytest

DIALECT = "https://json-schema.org/draft/2020-12/schema"


@pytest.fixture(autouse=True)
def _set_token():
    with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "test-token"}):
        yield


def _client():
    from mcp_server_tempest.server import mcp

    return fastmcp.Client(mcp)


async def test_negative_station_id_returns_structured_invalid_argument():
    async with _client() as c:
        r = await c.call_tool(
            "get_observation",
            {"station_id": -5},
            raise_on_error=False,  # renamed to tempest_* in Task 3
        )
    assert r.is_error
    payload = json.loads(r.content[0].text)
    assert payload["code"] == "invalid_argument"
    assert payload["field"] == "station_id"
    assert payload["value"] == -5
    assert payload["temporary"] is False
    assert "request_id" in payload


async def test_unknown_argument_returns_structured_invalid_argument():
    async with _client() as c:
        r = await c.call_tool(
            "get_stations", {"bogus": 1}, raise_on_error=False
        )  # renamed to tempest_* in Task 3
    assert r.is_error
    payload = json.loads(r.content[0].text)
    assert payload["code"] == "invalid_argument"
    assert payload["field"] == "bogus"


async def test_every_tool_advertises_schema_dialect():
    async with _client() as c:
        tools = await c.list_tools()
    assert tools
    for t in tools:
        assert t.inputSchema.get("$schema") == DIALECT, t.name
        assert (t.outputSchema or {}).get("$schema") == DIALECT, t.name
