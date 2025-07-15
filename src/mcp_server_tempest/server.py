import os
from typing import Annotated, Any, Dict

from cachetools import TTLCache
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from .models import (
    ForecastResponse,
    ObservationResponse,
    StationResponse,
    StationsResponse,
)

from .rest import (
    api_get_forecast,
    api_get_observation,
    api_get_station_id,
    api_get_stations,
)

cache = TTLCache(maxsize=100, ttl=60 * 5)

# Create the MCP server
mcp = FastMCP(
    name="WeatherFlow Tempest API Server",
    instructions="""
    This server provides access to WeatherFlow Tempest weather station data.
    Use get_stations() first to discover available stations, then use their IDs
    to get forecasts, observations, or detailed station information.
    Be aware that all weather data is returned in the units specified by each station.
    This is included in either the `units` dictionary or the `station_units` dictionary.
    For example, if the `units` dictionary specifies that the temperature units (`units_temp`) are 'f' for Fahrenheit,
    then you should report the temperature in Fahrenheit. If the user requests a different unit of measurement,
    you should convert the value to the requested unit.

    The user will only have access to data fromthe stations that they own.
    If the user does not have access to the given station, the request will fail with a "Not Found" error.
    When this happens, inform the user that the API key provided may not be valid for the given station.

    Tools:
    - get_stations(): Get a list of the weather stations that the user has access to.
    - get_station_id(): Get information about a specific weather station.
    - get_forecast(): Get the forecast and current conditions for a specific weather station.
    - get_observation(): Get the latest detailed observations for a specific weather station.

    Resources:
    - weather://tempest/stations: Get a list of the weather stations that the user has access to.
    - weather://tempest/stations/{station_id}: Get information about a specific weather station.
    - weather://tempest/forecast/{station_id}: Get the forecast for a specific weather station. This also includes current conditions.
    - weather://tempest/observations/{station_id}: Get the latest detailed observations for a specific weather station.
    """,
)


def _get_api_token(env_var: str = "WEATHERFLOW_API_TOKEN") -> str:
    if not (token := os.getenv(env_var)):
        raise ToolError(
            f"No Tempest API token found. This should be configured using the `{env_var}` environment variable."
        )
    return token


async def _get_stations_data(ctx: Context, use_cache: bool = True) -> StationsResponse:
    """Shared logic for getting stations data."""
    token = _get_api_token()

    if use_cache and "stations" in cache:
        await ctx.info("Using cached station data")
        return cache["stations"]

    await ctx.info("Getting available stations via the Tempest API")
    result = await api_get_stations(token)
    cache["stations"] = StationsResponse(**result)
    return cache["stations"]


async def _get_station_id_data(
    station_id: int, ctx: Context, use_cache: bool = True
) -> StationResponse:
    """Shared logic for getting station ID data."""
    token = _get_api_token()

    cache_id = f"station_id_{station_id}"

    if use_cache and cache_id in cache:
        await ctx.info(f"Using cached station data for station {station_id}")
        return cache[cache_id]

    await ctx.info(
        f"Getting station ID data for station {station_id} via the Tempest API"
    )
    result = await api_get_station_id(station_id, token)
    cache[cache_id] = StationResponse(**result)
    return cache[cache_id]


async def _get_forecast_data(
    station_id: int, ctx: Context, use_cache: bool = True
) -> ForecastResponse:
    """Shared logic for getting forecast data."""
    token = _get_api_token()

    cache_id = f"forecast_{station_id}"
    if use_cache and cache_id in cache:
        await ctx.info(f"Using cached forecast data for station {station_id}")
        return cache[cache_id]

    await ctx.info(f"Getting forecast for station {station_id} via the Tempest API")
    result = await api_get_forecast(station_id, token)
    cache[cache_id] = ForecastResponse(**result)
    return cache[cache_id]


async def _get_observation_data(
    station_id: int, ctx: Context, use_cache: bool = True
) -> ObservationResponse:
    """Shared logic for getting observation data."""
    token = _get_api_token()

    cache_id = f"observation_{station_id}"
    if use_cache and cache_id in cache:
        await ctx.info(f"Using cached observation data for station {station_id}")
        return cache[cache_id]

    await ctx.info(f"Getting observations for station {station_id} via the Tempest API")
    result = await api_get_observation(station_id, token)
    cache[cache_id] = ObservationResponse(**result)
    return cache[cache_id]


@mcp.tool(
    annotations={
        "title": "Get Weather Stations",
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": False,
    }
)
async def get_stations(
    use_cache: Annotated[
        bool,
        Field(
            default=True,
            description="Whether to use the cache to store the results of the request (default: True)",
        ),
    ],
    ctx: Context = None,
) -> StationsResponse:
    """
    Retrieve a list of the weather stations that the user has access to.

    Get station metadata and metadata for the Devices in it. Each user
    can create multiple Stations. A Device can only be in one Station at a
    time. Only devices with a serial_number value can submit new observations.
    A Device wihout a serial_number indicates that Device is no longer active.

    Args:
        use_cache (bool): Whether to use the cache to store the results of the request
          (default: True). Typically, stations do not change frequently, so this
          is a good way to avoid making unnecessary API calls.

    Returns:
        StationsResponse object containing the list of stations and API status

    """

    try:
        return await _get_stations_data(ctx, use_cache)
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.tool(
    annotations={
        "title": "Get Weather Station Information",
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": False,
    }
)
async def get_station_id(
    station_id: Annotated[
        int, Field(description="The station ID to get information for")
    ],
    use_cache: Annotated[
        bool,
        Field(
            default=True,
            description="Whether to use the cache to store the results of the request (default: True)",
        ),
    ],
    ctx: Context = None,
) -> StationResponse:
    """Get information about a specific weather station

    Args:
        station_id (int): The station ID to get information for
        use_cache (bool): Whether to use the cache to store the results of the request (default: True).
          Station configurations do not typicallychange frequently, so this is a good way to avoid
          making unnecessary API calls.

    Returns:
        A StationResponse object containing comprehensive station metadata and device information
    """
    try:
        return await _get_station_id_data(station_id, ctx, use_cache)
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.tool(
    annotations={
        "title": "Get Weather Forecast for a Station",
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": False,
    }
)
async def get_forecast(
    station_id: Annotated[
        int, Field(description="The ID of the station to get forecast for")
    ],
    use_cache: Annotated[
        bool,
        Field(
            default=True,
            description="Whether to use the cache to store the results of the request (default: True)",
        ),
    ],
    ctx: Context = None,
) -> ForecastResponse:
    """Get the forecast and current conditions for a specific weather station

    Args:
        station_id (int): The ID of the station to get information for
        use_cache (bool): Whether to use the cache to store the results of the request (default: True)

    Returns:
        ForecastResponse object containing the weather forecast and current conditions
    """
    try:
        return await _get_forecast_data(station_id, ctx, use_cache)
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.tool(
    annotations={
        "title": "Get Current Weather Observations for a Station",
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": False,
    }
)
async def get_observation(
    station_id: Annotated[
        int, Field(description="The ID of the station to get observations for")
    ],
    use_cache: Annotated[
        bool,
        Field(
            default=True,
            description="Whether to use the cache to store the results of the request (default: True)",
        ),
    ],
    ctx: Context = None,
) -> ObservationResponse:
    """Get recent detailed observations for a specific weather station

    Observations contain the most recent weather conditions at the given station.

    Args:
        station_id (int): The ID of the station to get information for
        use_cache (bool): Whether to use the cache to store the results of the request (default: True)

    Returns:
        ObservationResponse object containing the current weather observations and station metadata
    """

    try:
        return await _get_observation_data(station_id, ctx, use_cache)
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.tool(
    annotations={
        "title": "Clear the Weather Data Cache",
        "readOnlyHint": False,
        "openWorldHint": False,
        "idempotentHint": True,
    }
)
async def clear_cache(ctx: Context = None) -> str:
    """Clear the weather data cache (development tool)"""
    cache.clear()
    if ctx:
        await ctx.info("Cache cleared")
    return "Cache cleared successfully"


@mcp.resource(
    uri="weather://tempest/stations",
    name="Get Weather Stations",
    mime_type="application/json",
)
async def get_stations_resource(ctx: Context = None) -> StationsResponse:
    """Get a list of all your WeatherFlow stations.

    This resource can be used to get a list of all of the configured weather stations that the user has access to, along with all connected devices.
    Each result contains information about the station, including its name, location, devices, state, and more.
    A Device wihout a serial_number indicates that Device is no longer active.

    Returns:
        StationsResponse object containing the list of stations and API status
    """
    try:
        return await _get_stations_data(ctx, use_cache=True)
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.resource(
    uri="weather://tempest/stations/{station_id}",
    name="GetWeatherStationByID",
    mime_type="application/json",
)
async def get_station_id_resource(
    station_id: Annotated[
        int, Field(description="The ID of the station to get station information for")
    ],
    ctx: Context = None,
) -> StationResponse:
    """Get information and devices for a specific weather station

    This resource can be used to get a list of all of the configured weather stations that the user has access to, along with all connected devices.
    Each result contains information about the station, including its name, location, devices, state, and more.
    A Device wihout a serial_number indicates that Device is no longer active.

    Args:
        station_id (int): The ID of the station to get information for

    Returns:
        StationResponse object containing comprehensive station metadata and device information
    """

    try:
        return await _get_station_id_data(station_id, ctx, use_cache=True)
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.resource(
    uri="weather://tempest/forecast/{station_id}",
    name="GetWeatherForecast",
    mime_type="application/json",
)
async def get_forecast_resource(
    station_id: Annotated[
        int, Field(description="The ID of the station to get forecast for")
    ],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Get information and devices for a specific weather station

    This resource allows the user to retrieve the weather forecast from the specified weather station.

    Args:
        station_id (int): The ID of the station to get information for

    Returns:
        ForecastResponse object containing the weather forecast and current conditions
    """

    try:
        return await _get_forecast_data(station_id, ctx, use_cache=True)
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.resource(
    uri="weather://tempest/observations/{station_id}",
    name="GetWeatherObservations",
    mime_type="application/json",
)
async def get_observation_resource(
    station_id: Annotated[
        int, Field(description="The ID of the station to get observations for")
    ],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Get latest detailed observations for a specific weather station

    This resource allows the user to retrieve the weather forecast from the specified weather station.

    Returns:
        ObservationResponse object containing the current weather observations and station metadata
    """

    try:
        return await _get_observation_data(station_id, ctx, use_cache=True)
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


if __name__ == "__main__":
    mcp.run()
