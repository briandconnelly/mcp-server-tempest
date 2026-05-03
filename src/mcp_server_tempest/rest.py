import math
from collections.abc import Mapping

from weatherflow4py.api import WeatherFlowRestAPI


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


async def api_get_stations(token: str) -> dict:
    async with WeatherFlowRestAPI(token) as api:
        stations = await api.async_get_stations()
        return stations.to_dict()


async def api_get_station_id(station_id: int, token: str) -> dict:
    async with WeatherFlowRestAPI(token) as api:
        station = await api.async_get_station(station_id=station_id)
        if not station:
            raise ValueError(f"No station found with ID {station_id}")
        return station[0].to_dict()


async def api_get_forecast(station_id: int, token: str) -> dict:
    async with WeatherFlowRestAPI(token) as api:
        forecast = await api.async_get_forecast(station_id=station_id)
        return forecast.to_dict()


async def api_get_observation(station_id: int, token: str) -> dict:
    async with WeatherFlowRestAPI(token) as api:
        observation = await api.async_get_observation(station_id=station_id)
        return observation.to_dict()
