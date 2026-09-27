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
    # #78: the envelope must also be in structuredContent, not just text.
    assert r.structured_content == payload


async def test_negative_station_id_carries_structured_content_at_wire_level():
    # Same case as above, but via the raw MCP protocol result (no FastMCP
    # client-side parsing) to lock in that isError and structuredContent
    # both survive on the wire (#78). The SDK exposes them as snake_case
    # attributes; the wire keys stay camelCase..
    async with _client() as c:
        raw = await c.call_tool_mcp("tempest_get_observation", {"station_id": -5})
    assert raw.is_error is True
    assert raw.structured_content is not None
    text_payload = json.loads(raw.content[0].text)
    assert raw.structured_content == text_payload
    assert text_payload["code"] == "invalid_argument"
    assert text_payload["field"] == "station_id"


async def test_unknown_argument_returns_structured_invalid_argument():
    async with _client() as c:
        r = await c.call_tool("tempest_get_stations", {"bogus": 1}, raise_on_error=False)
    assert r.is_error
    payload = json.loads(r.content[0].text)
    assert payload["code"] == "invalid_argument"
    assert payload["details"]["unknown_argument"] == "bogus"
    assert "field" not in payload


async def test_unknown_secret_named_arg_value_not_reflected():
    # A secret misplaced as an unknown argument must not be echoed back into
    # model context / transcripts / client logs (issue #57).
    secret = "sk-super-secret-value"
    async with _client() as c:
        r = await c.call_tool("tempest_get_stations", {"api_token": secret}, raise_on_error=False)
    assert r.is_error
    payload = json.loads(r.content[0].text)
    assert payload["code"] == "invalid_argument"
    assert payload["details"]["unknown_argument"] == "api_token"
    assert "field" not in payload
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
    from mcp_server_tempest.errors import ErrorCode, WeatherFlowError, list_stations_repair

    wfe = WeatherFlowError(
        code=ErrorCode.STATION_NOT_FOUND,
        message="Station not found.",
        hint="Call tempest_get_stations to list valid station_ids.",
        field_name="station_id",
        value=99999,
        repair=list_stations_repair(),
    )
    with patch("mcp_server_tempest.server.api_get_observation", side_effect=wfe):
        async with _client() as c:
            r = await c.call_tool(
                "tempest_get_observation", {"station_id": 99999}, raise_on_error=False
            )
    assert r.is_error
    payload = json.loads(r.content[0].text)
    assert payload["code"] == "station_not_found"
    assert payload["repair"] == list_stations_repair()
    assert "tempest_get_stations" in payload["hint"]
    assert payload["temporary"] is False
    assert "request_id" in payload
    # #78: the envelope must also be in structuredContent, not just text.
    assert r.structured_content == payload


async def test_every_tool_advertises_schema_dialect():
    async with _client() as c:
        tools = await c.list_tools()
    assert tools
    for t in tools:
        assert t.input_schema.get("$schema") == DIALECT, t.name
        assert (t.output_schema or {}).get("$schema") == DIALECT, t.name


async def test_every_tool_description_states_station_scope():
    async with _client() as c:
        tools = await c.list_tools()
    for t in tools:
        assert "not a global" in (t.description or "").lower(), t.name


async def _call(name, args):
    async with _client() as c:
        r = await c.call_tool(name, args, raise_on_error=False)
    assert r.is_error
    return json.loads(r.content[0].text), r.content[0].text


async def test_out_of_range_hours_repairs_to_bound_preserving_intent():
    payload, _ = await _call(
        "tempest_get_forecast", {"station_id": 1, "hours": 100, "detailed": True}
    )
    assert payload["repair"] == {
        "next_step": "retry_with_corrected_arguments",
        "tool": "tempest_get_forecast",
        "arguments": {"station_id": 1, "detailed": True, "hours": 48},
    }


async def test_below_minimum_hours_repairs_to_lower_bound():
    payload, _ = await _call("tempest_get_forecast", {"station_id": 1, "hours": 0})
    assert payload["repair"]["arguments"] == {"station_id": 1, "hours": 1}


async def test_repair_fixes_every_invalid_argument_at_once():
    # Pydantic reports both errors; a repair that fixed only `hours` would
    # hand the agent a retry that fails again on `days`.
    payload, _ = await _call("tempest_get_forecast", {"station_id": 1, "hours": 100, "days": 0})
    assert payload["details"]["error_count"] == 2
    assert payload["repair"] == {
        "next_step": "retry_with_corrected_arguments",
        "tool": "tempest_get_forecast",
        "arguments": {"station_id": 1, "hours": 48, "days": 1},
    }


async def test_bad_station_id_repairs_via_station_lookup():
    for args in ({"station_id": -5}, {}):
        payload, _ = await _call("tempest_get_observation", args)
        assert payload["repair"] == {
            "next_step": "list_stations",
            "tool": "tempest_get_stations",
            "arguments": {},
        }


async def test_unparseable_optional_argument_repairs_by_omission():
    payload, _ = await _call("tempest_get_forecast", {"station_id": 1, "hours": "abc"})
    assert payload["repair"] == {
        "next_step": "retry_without_invalid_arguments",
        "tool": "tempest_get_forecast",
        "arguments": {"station_id": 1},
    }


async def test_repair_never_carries_unknown_or_string_arguments():
    # Review Focus #1.
    secret = "sk-super-secret-value"
    payload, text = await _call("tempest_get_observation", {"station_id": 1, "api_token": secret})
    assert "field" not in payload
    assert payload["details"]["unknown_argument"] == "api_token"
    assert payload["repair"] == {
        "next_step": "retry_without_unknown_arguments",
        "tool": "tempest_get_observation",
        "arguments": {"station_id": 1},
    }
    assert secret not in text


async def test_numeric_unknown_argument_value_not_reflected():
    # Review Focus #4: FastMCP 4 reports unexpected_keyword_argument.
    payload, _ = await _call("tempest_get_capabilities", {"bogus": 1})
    assert "value" not in payload
    assert payload["repair"] == {
        "next_step": "retry_without_unknown_arguments",
        "tool": "tempest_get_capabilities",
        "arguments": {},
    }
