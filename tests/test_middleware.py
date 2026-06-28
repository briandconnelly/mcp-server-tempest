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
            "tempest_get_observation",
            {"station_id": -5},
            raise_on_error=False,
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
        r = await c.call_tool("tempest_get_stations", {"bogus": 1}, raise_on_error=False)
    assert r.is_error
    payload = json.loads(r.content[0].text)
    assert payload["code"] == "invalid_argument"
    assert payload["field"] == "bogus"


async def test_unknown_secret_named_arg_value_not_reflected():
    # A secret misplaced as an unknown argument must not be echoed back into
    # model context / transcripts / client logs (issue #57).
    secret = "sk-super-secret-value"
    async with _client() as c:
        r = await c.call_tool("tempest_get_stations", {"api_token": secret}, raise_on_error=False)
    assert r.is_error
    payload = json.loads(r.content[0].text)
    assert payload["code"] == "invalid_argument"
    assert payload["field"] == "api_token"
    assert "value" not in payload
    assert secret not in r.content[0].text


async def test_string_value_for_known_int_field_not_reflected():
    # All tool inputs are numeric/bool; a string is never legitimate and is the
    # secret-leak vector, so its value is dropped (issue #57).
    secret = "sk-secret-as-station-id"
    async with _client() as c:
        r = await c.call_tool(
            "tempest_get_observation", {"station_id": secret}, raise_on_error=False
        )
    assert r.is_error
    payload = json.loads(r.content[0].text)
    assert payload["code"] == "invalid_argument"
    assert payload["field"] == "station_id"
    assert "value" not in payload
    assert secret not in r.content[0].text


async def test_tools_use_tempest_prefix():
    async with _client() as c:
        names = {t.name for t in await c.list_tools()}
    assert names == {
        "tempest_get_stations",
        "tempest_get_station_details",
        "tempest_get_observation",
        "tempest_get_forecast",
        "tempest_get_capabilities",
    }


async def test_station_not_found_repair_references_prefixed_name():
    from mcp_server_tempest.errors import ErrorCode, WeatherFlowError

    wfe = WeatherFlowError(
        code=ErrorCode.STATION_NOT_FOUND,
        message="Station not found.",
        hint="Call tempest_get_stations to list valid station_ids.",
        field_name="station_id",
        value=99999,
        next={"tool": "tempest_get_stations"},
    )
    with patch("mcp_server_tempest.server.api_get_observation", side_effect=wfe):
        async with _client() as c:
            r = await c.call_tool(
                "tempest_get_observation", {"station_id": 99999}, raise_on_error=False
            )
    payload = json.loads(r.content[0].text)
    assert payload["code"] == "station_not_found"
    assert payload["next"] == {"tool": "tempest_get_stations"}
    assert "tempest_get_stations" in payload["hint"]


async def test_every_tool_advertises_schema_dialect():
    async with _client() as c:
        tools = await c.list_tools()
    assert tools
    for t in tools:
        assert t.inputSchema.get("$schema") == DIALECT, t.name
        assert (t.outputSchema or {}).get("$schema") == DIALECT, t.name


async def test_every_tool_description_states_station_scope():
    async with _client() as c:
        tools = await c.list_tools()
    for t in tools:
        assert "not a global" in (t.description or "").lower(), t.name
