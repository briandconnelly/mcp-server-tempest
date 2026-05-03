"""End-to-end boundary tests for the structured-error contract.

These exercise the public tool surface (get_stations, get_station_details,
get_forecast, get_observation) and assert against the JSON payload that
clients actually receive in ToolError.args[0]. Patches target
`mcp_server_tempest.server.api_*` because server.py rebinds the import
(see tests/test_server.py:324, 346, 447, 456, 569 for the convention).
"""

import json
import os
from unittest.mock import MagicMock, patch

import aiohttp
import pytest
from fastmcp.exceptions import ToolError

import mcp_server_tempest.server as server_module
from mcp_server_tempest.errors import ErrorCode, WeatherFlowError
from mcp_server_tempest.server import (
    cache,
    get_forecast,
    get_observation,
    get_station_details,
    get_stations,
)


@pytest.fixture(autouse=True)
def _set_token():
    with patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "test-token"}):
        yield


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    server_module.disk_cache = None
    with patch.object(server_module, "_get_disk_cache", return_value=None):
        yield
    cache.clear()
    server_module.disk_cache = None


def _make_response_error(status: int, headers: dict[str, str] | None = None):
    return aiohttp.ClientResponseError(
        request_info=MagicMock(spec=aiohttp.RequestInfo),
        history=(),
        status=status,
        message=f"HTTP {status}",
        headers=headers or {},
    )


async def _payload_from(coro_factory):
    with pytest.raises(ToolError) as excinfo:
        await coro_factory()
    return json.loads(excinfo.value.args[0])


# -- Per-code "one happy invalid call" boundary tests --


class TestAuthMissingBoundary:
    async def test_unset_env_var(self):
        with patch.dict(os.environ, {}, clear=True):
            payload = await _payload_from(lambda: get_stations())
        assert payload["code"] == "auth_missing"
        assert payload["temporary"] is False
        assert "WEATHERFLOW_API_TOKEN" in payload["message"]


class TestAuthInvalidBoundary:
    async def test_auth_invalid_via_weatherflow_error(self):
        # Mock at the server-bound symbol (not rest.*) since server.py rebinds
        # the import. WeatherFlowError flows through _dispatch unchanged.
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            side_effect=WeatherFlowError(
                code=ErrorCode.AUTH_INVALID,
                message="bad token",
                hint="get a new one",
            ),
        ):
            payload = await _payload_from(lambda: get_stations())
        assert payload["code"] == "auth_invalid"
        assert payload["hint"] == "get a new one"


class TestAuthForbiddenBoundary:
    async def test_403_on_observation_recommends_get_stations(self):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            side_effect=WeatherFlowError(
                code=ErrorCode.AUTH_FORBIDDEN,
                message="no access",
                hint="verify ownership",
                next={"tool": "get_stations"},
            ),
        ):
            payload = await _payload_from(lambda: get_observation(station_id=12345))
        assert payload["code"] == "auth_forbidden"
        assert payload["next"] == {"tool": "get_stations"}

    async def test_403_on_get_stations_no_next(self):
        with patch(
            "mcp_server_tempest.server.api_get_stations",
            side_effect=WeatherFlowError(
                code=ErrorCode.AUTH_FORBIDDEN,
                message="scope",
                hint="verify token scope",
            ),
        ):
            payload = await _payload_from(lambda: get_stations())
        assert payload["code"] == "auth_forbidden"
        assert "next" not in payload


class TestStationNotFoundBoundary:
    async def test_404_on_observation_includes_value(self):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            side_effect=WeatherFlowError(
                code=ErrorCode.STATION_NOT_FOUND,
                message="not found",
                hint="call get_stations",
                field_name="station_id",
                value=99999,
                next={"tool": "get_stations"},
            ),
        ):
            payload = await _payload_from(lambda: get_observation(station_id=99999))
        assert payload["code"] == "station_not_found"
        assert payload["field"] == "station_id"
        assert payload["value"] == 99999
        assert payload["next"] == {"tool": "get_stations"}


class TestRateLimitedBoundary:
    async def test_429_with_retry_after_ms(self):
        with patch(
            "mcp_server_tempest.server.api_get_forecast",
            side_effect=WeatherFlowError(
                code=ErrorCode.RATE_LIMITED,
                message="slow down",
                hint="wait",
                retry_after_ms=5000,
            ),
        ):
            payload = await _payload_from(lambda: get_forecast(station_id=12345))
        assert payload["code"] == "rate_limited"
        assert payload["temporary"] is True
        assert payload["retry_after_ms"] == 5000


class TestUpstreamUnavailableBoundary:
    async def test_503_is_temporary(self):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            side_effect=WeatherFlowError(
                code=ErrorCode.UPSTREAM_UNAVAILABLE,
                message="api down",
                hint="retry shortly",
            ),
        ):
            payload = await _payload_from(lambda: get_observation(station_id=12345))
        assert payload["code"] == "upstream_unavailable"
        assert payload["temporary"] is True


class TestUpstreamInvalidResponseBoundary:
    async def test_parse_failure(self):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            side_effect=WeatherFlowError(
                code=ErrorCode.UPSTREAM_INVALID_RESPONSE,
                message="bad payload",
                hint="report",
                details={"exception_type": "ValueError"},
            ),
        ):
            payload = await _payload_from(lambda: get_observation(station_id=12345))
        assert payload["code"] == "upstream_invalid_response"
        assert payload["temporary"] is False
        assert payload["details"]["exception_type"] == "ValueError"


class TestInternalErrorBoundary:
    async def test_unexpected_exception_does_not_leak(self):
        with patch(
            "mcp_server_tempest.server.api_get_observation",
            side_effect=ValueError("internal kaboom secret"),
        ):
            payload = await _payload_from(lambda: get_observation(station_id=12345))
        assert payload["code"] == "internal_error"
        assert "kaboom" not in payload["message"]
        assert "kaboom" not in payload.get("hint", "")


# -- Behavioral no-bare-exception regression --


@pytest.mark.parametrize(
    "tool_callable, kwargs, helper_name",
    [
        (get_stations, {}, "_get_stations_data"),
        (get_station_details, {"station_id": 12345}, "_get_station_details_data"),
        (get_forecast, {"station_id": 12345}, "_get_forecast_data"),
        (get_observation, {"station_id": 12345}, "_get_observation_data"),
    ],
)
async def test_every_tool_wraps_in_dispatch(tool_callable, kwargs, helper_name):
    """A tool that forgets to wrap its body in _dispatch will let bare
    exceptions escape. Mock its data-helper to raise ValueError; the
    tool MUST return an internal_error JSON payload, not let the bare
    ValueError out."""

    async def boom(*_a, **_kw):
        raise ValueError("bare exception escaped")

    with patch(f"mcp_server_tempest.server.{helper_name}", new=boom):
        with pytest.raises(ToolError) as excinfo:
            await tool_callable(**kwargs)
        payload = json.loads(excinfo.value.args[0])
        assert payload["code"] == "internal_error", (
            f"{tool_callable.__name__} forgot _dispatch; got {payload!r}"
        )
        assert "bare exception escaped" not in payload["message"]
