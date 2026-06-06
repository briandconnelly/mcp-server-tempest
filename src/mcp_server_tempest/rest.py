import json
import math
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from typing import Any, Literal

import aiohttp
from marshmallow.exceptions import MarshmallowError
from weatherflow4py.api import WeatherFlowRestAPI

from .errors import ErrorCode, WeatherFlowError

# Total per-request budget for an upstream WeatherFlow call. weatherflow4py
# creates its own aiohttp session with NO timeout (aiohttp would otherwise
# default to ~5 min) and — worse — its `__aexit__` is a no-op that never closes
# that session, so `async with WeatherFlowRestAPI(token)` leaks a session on
# every call. We therefore own the session here: bound it with an explicit
# timeout and close it deterministically. Surfaced to agents via
# capabilities()["latency"]; a breach maps to upstream_unavailable
# (temporary: true), so the repair is "retry with backoff".
_REQUEST_TIMEOUT_SECONDS = 15
_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=_REQUEST_TIMEOUT_SECONDS)


@asynccontextmanager
async def _api_session(token: str) -> AsyncIterator[Any]:
    """Yield a WeatherFlowRestAPI bound to a timeout-scoped session we own.

    The session is created and closed here (weatherflow4py won't close a
    caller-provided session), so no aiohttp session leaks across calls.

    Yields `Any` rather than `WeatherFlowRestAPI`: weatherflow4py's response
    models are not fully typed (their runtime `.to_dict()` / indexing is absent
    from the declared types), so a precise handle type makes `ty` reject the
    `.to_dict()` calls below for methods that genuinely exist at runtime.
    """
    async with aiohttp.ClientSession(timeout=_REQUEST_TIMEOUT) as session:
        async with WeatherFlowRestAPI(token, session=session) as api:
            yield api


# Parse-failure exception types from `weatherflow4py.api._make_request()`'s
# `response_model.from_json(data)` step. We catch a narrow set so genuine
# server-side defects (KeyError, AttributeError, etc.) propagate to
# `_dispatch`'s internal_error boundary instead of getting misclassified as
# upstream_invalid_response. Add new types here only if observed in production.
_PARSE_FAILURE_EXCEPTIONS: tuple[type[Exception], ...] = (
    MarshmallowError,
    json.JSONDecodeError,
)


def _retry_after_ms(headers: Mapping[str, str] | None) -> int | None:
    """Parse a `Retry-After` header value to milliseconds.

    Numeric-seconds form only (RFC 9110 §10.2.3 `delay-seconds`).
    HTTP-date form, negative values, and non-finite values (`inf`/`nan`)
    return None — agents seeing `temporary: true` without `retry_after_ms`
    should treat it as 'retry with backoff' (see wire-contract policy
    in the spec).
    """
    if not headers:
        return None
    raw = headers.get("Retry-After")
    if not raw:
        return None
    try:
        seconds = float(raw)
    except ValueError:
        return None
    if not math.isfinite(seconds) or seconds < 0:
        return None
    return int(seconds * 1000)


# Operations that take a station_id and where 404 means "no such station".
_STATION_SCOPED: frozenset[str] = frozenset({"station", "forecast", "observation"})

Operation = Literal["stations", "station", "forecast", "observation"]

# URL repeated in every wrapper's parse-failure hint; lift to a constant so
# the repo move doesn't require touching four call sites.
_ISSUES_URL = "https://github.com/briandconnelly/mcp-server-tempest/issues"


def _translate_response_error(
    e: aiohttp.ClientResponseError,
    *,
    operation: Operation,
    station_id: int | None = None,
) -> WeatherFlowError:
    """Map an aiohttp HTTP error to a structured WeatherFlowError.

    `operation` is the canonical name of the WeatherFlow REST endpoint
    being called (`"stations"`, `"station"`, `"forecast"`, `"observation"`)
    and is used to vary 403/404 hints. `station_id` is threaded by
    station-scoped wrappers so the 404 branch can populate `value`.
    """
    status = e.status
    if status == 401:
        return WeatherFlowError(
            code=ErrorCode.AUTH_INVALID,
            message="WeatherFlow rejected the API token.",
            hint="Generate a new token at https://tempestwx.com/settings/tokens",
            details={"upstream_status": 401, "operation": operation},
        )
    if status == 403:
        if operation in _STATION_SCOPED:
            return WeatherFlowError(
                code=ErrorCode.AUTH_FORBIDDEN,
                message="Token does not have access to this station.",
                hint="Verify station ownership.",
                next={"tool": "tempest_get_stations"},
                details={"upstream_status": 403, "operation": operation},
            )
        return WeatherFlowError(
            code=ErrorCode.AUTH_FORBIDDEN,
            message="Token does not have access to this resource.",
            hint="Verify token scope.",
            details={"upstream_status": 403, "operation": operation},
        )
    if status == 404:
        if operation in _STATION_SCOPED:
            return WeatherFlowError(
                code=ErrorCode.STATION_NOT_FOUND,
                message="Station not found.",
                hint="Call tempest_get_stations to list valid station_ids.",
                field_name="station_id",
                value=station_id,
                next={"tool": "tempest_get_stations"},
                details={"upstream_status": 404, "operation": operation},
            )
        return WeatherFlowError(
            code=ErrorCode.UPSTREAM_INVALID_RESPONSE,
            message=f"Upstream returned 404 for operation {operation!r}.",
            details={"upstream_status": 404, "operation": operation},
        )
    if status == 429:
        return WeatherFlowError(
            code=ErrorCode.RATE_LIMITED,
            message="WeatherFlow rate limit hit.",
            hint="Wait retry_after_ms before retrying.",
            retry_after_ms=_retry_after_ms(e.headers),
            details={"upstream_status": 429, "operation": operation},
        )
    if 500 <= status < 600:
        return WeatherFlowError(
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
            message="WeatherFlow API is temporarily unavailable.",
            hint="Retry in a few seconds.",
            details={"upstream_status": status, "operation": operation},
        )
    return WeatherFlowError(
        code=ErrorCode.UPSTREAM_INVALID_RESPONSE,
        message=f"Unexpected upstream status {status}.",
        details={"upstream_status": status, "operation": operation},
    )


async def api_get_stations(token: str) -> dict:
    try:
        async with _api_session(token) as api:
            stations = await api.async_get_stations()
            return stations.to_dict()
    except aiohttp.ClientResponseError as e:
        raise _translate_response_error(e, operation="stations") from e
    except (TimeoutError, aiohttp.ClientError) as e:
        # transport / DNS / connection error, or our _REQUEST_TIMEOUT firing
        # (the total-timeout path raises asyncio.TimeoutError, which is
        # builtins.TimeoutError on 3.11+ and is NOT an aiohttp.ClientError).
        raise WeatherFlowError(
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
            message="Could not reach WeatherFlow API in time.",
            hint="Check network connectivity; retry.",
            details={"operation": "stations"},
        ) from e
    except WeatherFlowError:
        # Don't wrap our own typed errors — they already carry codes.
        raise
    except _PARSE_FAILURE_EXCEPTIONS as exc:
        # See _PARSE_FAILURE_EXCEPTIONS at top of module. Genuine server-side
        # defects propagate to _dispatch's internal_error boundary instead.
        raise WeatherFlowError(
            code=ErrorCode.UPSTREAM_INVALID_RESPONSE,
            message="Failed to parse WeatherFlow API response.",
            hint=f"Report at {_ISSUES_URL} if persistent.",
            details={"operation": "stations", "exception_type": type(exc).__name__},
        ) from exc


async def api_get_station_id(station_id: int, token: str) -> dict:
    try:
        async with _api_session(token) as api:
            station = await api.async_get_station(station_id=station_id)
            if not station:
                raise WeatherFlowError(
                    code=ErrorCode.STATION_NOT_FOUND,
                    message="Station not found.",
                    hint="Call tempest_get_stations to list valid station_ids.",
                    field_name="station_id",
                    value=station_id,
                    next={"tool": "tempest_get_stations"},
                    # No upstream_status — the API returned 200 with an empty list.
                    details={"operation": "station"},
                )
            return station[0].to_dict()
    except aiohttp.ClientResponseError as e:
        raise _translate_response_error(e, operation="station", station_id=station_id) from e
    except (TimeoutError, aiohttp.ClientError) as e:
        raise WeatherFlowError(
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
            message="Could not reach WeatherFlow API in time.",
            hint="Check network connectivity; retry.",
            details={"operation": "station"},
        ) from e
    except WeatherFlowError:
        raise
    except _PARSE_FAILURE_EXCEPTIONS as exc:
        raise WeatherFlowError(
            code=ErrorCode.UPSTREAM_INVALID_RESPONSE,
            message="Failed to parse WeatherFlow API response.",
            hint=f"Report at {_ISSUES_URL} if persistent.",
            details={"operation": "station", "exception_type": type(exc).__name__},
        ) from exc


async def api_get_forecast(station_id: int, token: str) -> dict:
    try:
        async with _api_session(token) as api:
            forecast = await api.async_get_forecast(station_id=station_id)
            return forecast.to_dict()
    except aiohttp.ClientResponseError as e:
        raise _translate_response_error(e, operation="forecast", station_id=station_id) from e
    except (TimeoutError, aiohttp.ClientError) as e:
        raise WeatherFlowError(
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
            message="Could not reach WeatherFlow API in time.",
            hint="Check network connectivity; retry.",
            details={"operation": "forecast"},
        ) from e
    except WeatherFlowError:
        raise
    except _PARSE_FAILURE_EXCEPTIONS as exc:
        raise WeatherFlowError(
            code=ErrorCode.UPSTREAM_INVALID_RESPONSE,
            message="Failed to parse WeatherFlow API response.",
            hint=f"Report at {_ISSUES_URL} if persistent.",
            details={"operation": "forecast", "exception_type": type(exc).__name__},
        ) from exc


async def api_get_observation(station_id: int, token: str) -> dict:
    try:
        async with _api_session(token) as api:
            observation = await api.async_get_observation(station_id=station_id)
            return observation.to_dict()
    except aiohttp.ClientResponseError as e:
        raise _translate_response_error(e, operation="observation", station_id=station_id) from e
    except (TimeoutError, aiohttp.ClientError) as e:
        raise WeatherFlowError(
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
            message="Could not reach WeatherFlow API in time.",
            hint="Check network connectivity; retry.",
            details={"operation": "observation"},
        ) from e
    except WeatherFlowError:
        raise
    except _PARSE_FAILURE_EXCEPTIONS as exc:
        raise WeatherFlowError(
            code=ErrorCode.UPSTREAM_INVALID_RESPONSE,
            message="Failed to parse WeatherFlow API response.",
            hint=f"Report at {_ISSUES_URL} if persistent.",
            details={"operation": "observation", "exception_type": type(exc).__name__},
        ) from exc
