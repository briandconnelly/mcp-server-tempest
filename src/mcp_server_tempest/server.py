"""
WeatherFlow Tempest MCP Server

This module provides a Model Context Protocol (MCP) server for accessing WeatherFlow Tempest
weather station data. It offers both tools (for interactive queries) and resources
(for data access) to retrieve real-time weather observations, forecasts, and station metadata.

Features:
- Real-time weather observations from personal weather stations
- Weather forecasts and current conditions
- Station and device metadata
- Automatic caching with configurable TTL
- Support for multiple stations per user account

Setup:
    1. Get an API token from https://tempestwx.com/settings/tokens
    2. Set the WEATHERFLOW_API_TOKEN environment variable
    3. Run the server: python -m weatherflow_mcp

Environment Variables:
    WEATHERFLOW_API_TOKEN: Your WeatherFlow API token (required)
    WEATHERFLOW_CACHE_TTL: Cache timeout in seconds (default: 300)
    WEATHERFLOW_CACHE_SIZE: Maximum cache entries (default: 100)

Example Usage:
    # Get available stations
    stations = await client.call_tool("get_stations")

    # Get current conditions for a specific station
    conditions = await client.call_tool("get_observation", {"station_id": 12345})

    # Access via resources
    forecast = await client.read_resource("weather://tempest/forecast/12345")
"""

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

cache = TTLCache(
    maxsize=os.getenv("WEATHERFLOW_CACHE_SIZE", 100),
    ttl=os.getenv("WEATHERFLOW_CACHE_TTL", 300),
)

# Create the MCP server
mcp = FastMCP(
    name="WeatherFlow Tempest API Server",
    instructions="""
    WeatherFlow Tempest weather station data server.
    
    🚀 Quick Start:
    1. Use get_stations() to see your available weather stations
    2. Use get_observation(station_id) to get current conditions
    3. Use get_forecast(station_id) to get weather forecasts
    
    💡 Pro Tips:
    - Data is cached for 5 minutes to improve performance
    - All measurements are in the units configured for each station
    - Use the 'units' or 'station_units' fields to understand the unit system
    - Station IDs are found in the get_stations() response
    
    🔧 Available Tools:
    - get_stations(): List your weather stations
    - get_observation(station_id): Current weather conditions  
    - get_forecast(station_id): Weather forecast
    - get_station_id(station_id): Station details and devices
    - clear_cache(): Clear the data cache (for testing)
    
    📊 Resource URIs:
    - weather://tempest/stations - List all stations
    - weather://tempest/observations/{station_id} - Current conditions
    - weather://tempest/forecast/{station_id} - Weather forecast
    - weather://tempest/help - Server documentation
    
    🔑 Setup: Set WEATHERFLOW_API_TOKEN environment variable
    Get your token at: https://tempestwx.com/settings/tokens
    """,
)


async def _get_api_token(env_var: str = "WEATHERFLOW_API_TOKEN") -> str:
    if not (token := os.getenv(env_var)):
        raise ToolError(
            f"WeatherFlow API token not configured. Please set the {env_var} environment variable. "
            f"You can get an API token from https://tempestwx.com/settings/tokens"
        )
    return token


async def _get_stations_data(ctx: Context, use_cache: bool = True) -> StationsResponse:
    """Shared logic for getting stations data."""
    token = await _get_api_token()

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
    token = await _get_api_token()

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
    token = await _get_api_token()

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
    token = await _get_api_token()

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
    """Get a list of all weather stations accessible with your API token.

    This is typically the first function you should call to discover what weather
    stations are available to you. Each station contains one or more devices that
    collect different types of weather data.

    The response includes comprehensive information about each station:
    - Station metadata (name, location, timezone, elevation)
    - Connected devices and their capabilities
    - Device status and last communication times
    - Station configuration and settings

    **Device Types:**
    - **Tempest**: All-in-one weather sensor (wind, rain, temperature, etc.)
    - **Air**: Temperature, humidity, pressure, lightning detection
    - **Sky**: Wind, rain, solar radiation, UV index
    - **Hub**: Communication hub for other devices

    **Active vs Inactive Devices:**
    Devices with a `serial_number` are active and collecting data.
    Devices without a `serial_number` are no longer active or have been removed.

    Args:
        use_cache: Whether to use cached station data. Since station configurations
                  rarely change, caching improves performance and reduces API calls.
                  Cache expires after 5 minutes.

    Returns:
        StationsResponse containing:
        - List of stations with metadata and device information
        - API status and response metadata
        - Station-specific settings like units and location data

    Raises:
        ToolError: If API token is invalid, network request fails, or you have
                  no accessible stations

    Example Usage:
        >>> stations = await get_stations()
        >>> for station in stations.stations:
        >>>     print(f"Station: {station.name} (ID: {station.station_id})")
        >>>     print(f"Location: {station.latitude}, {station.longitude}")
        >>>     for device in station.devices:
        >>>         if device.serial_number:  # Active device
        >>>             print(f"  Device: {device.device_type}")

    Note:
        Station IDs returned by this function are used in other tools like
        get_observation(), get_forecast(), and get_station_id().
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
        int, Field(description="The station ID to get information for", gt=0)
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
    """Get comprehensive details and configuration for a specific weather station.

    This function provides in-depth information about a single weather station,
    including all connected devices, detailed configuration settings, and
    operational status. Use this when you need complete station metadata
    beyond what get_stations() provides.

    **Station Information Includes:**
    - Complete station metadata (name, location, elevation, timezone)
    - Detailed device inventory with specifications and status
    - Station configuration and measurement units
    - Device communication history and health status
    - Public/private settings and sharing permissions

    **Device Details Include:**
    - Device type, model, and firmware version
    - Serial numbers and hardware revisions
    - Last communication timestamps
    - Device-specific settings and capabilities
    - Calibration and sensor health information

    **Operational Status:**
    - Online/offline status for each device
    - Battery levels (for battery-powered devices)
    - Signal strength and communication quality
    - Data collection intervals and settings

    Args:
        station_id: The numeric identifier of the station. Get this from
                   get_stations() or from your WeatherFlow account dashboard.
        use_cache: Whether to use cached station data. Station configurations
                  change infrequently, so caching improves performance.
                  Cache expires after 5 minutes.

    Returns:
        StationResponse containing:
        - Complete station metadata and settings
        - Detailed device inventory and status
        - Configuration parameters and unit settings
        - API response metadata

    Raises:
        ToolError: If the station ID doesn't exist, you don't have access to it,
                  API token is invalid, or network request fails

    Example Usage:
        >>> station = await get_station_id(12345)
        >>> print(f"Station: {station.name}")
        >>> print(f"Location: {station.latitude}°, {station.longitude}°")
        >>> print(f"Elevation: {station.station_meta.elevation}m")
        >>> print(f"Units: {station.station_units}")
        >>>
        >>> # Check device status
        >>> for device in station.devices:
        >>>     if device.serial_number:
        >>>         status = "Online" if device.device_meta else "Offline"
        >>>         print(f"  {device.device_type}: {status}")

    Note:
        Use get_stations() first to discover available station IDs. This function
        provides more detailed information than the station list overview.
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
        int, Field(description="The ID of the station to get forecast for", gt=0)
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
    """Get weather forecast and current conditions for a specific weather station.

    This function retrieves comprehensive weather forecast data including current
    conditions, hourly forecasts, and daily summaries. The forecast combines
    data from your personal weather station with professional weather models
    to provide hyper-local predictions.

    **Current Conditions Include:**
    - Real-time temperature, humidity, and pressure
    - Wind speed, direction, and gusts
    - Precipitation rate and accumulation
    - Solar radiation and UV index
    - Visibility and weather conditions
    - "Feels like" temperature and comfort indices

    **Forecast Data Includes:**
    - Hourly forecasts for the next 24-48 hours
    - Daily forecasts for the next 7-10 days
    - Temperature highs and lows
    - Precipitation probability and amounts
    - Wind forecasts and weather condition summaries
    - Sunrise/sunset times and moon phases

    **Data Sources:**
    The forecast combines your station's real-time observations with
    professional meteorological models to provide accurate local predictions
    that account for your specific microclimate and terrain.

    Args:
        station_id: The numeric identifier of the weather station. Get this from
                   get_stations() or your WeatherFlow account dashboard.
        use_cache: Whether to use cached forecast data. Forecasts update
                  frequently, but caching for a few minutes improves performance
                  for repeated requests. Cache expires after 5 minutes.

    Returns:
        ForecastResponse containing:
        - Current weather conditions and observations
        - Hourly forecast data for the next 24-48 hours
        - Daily forecast summaries for the next week
        - Station location and unit information
        - Forecast generation timestamp and metadata

    Raises:
        ToolError: If the station ID doesn't exist, you don't have access to it,
                  API token is invalid, or network request fails

    Example Usage:
        >>> forecast = await get_forecast(12345)
        >>>
        >>> # Current conditions
        >>> current = forecast.current_conditions
        >>> print(f"Current: {current.air_temperature}° {forecast.units.units_temp}")
        >>> print(f"Conditions: {current.conditions}")
        >>> print(f"Wind: {current.wind_avg} {forecast.units.units_wind}")
        >>>
        >>> # Today's forecast
        >>> today = forecast.forecast.daily[0]
        >>> print(f"High/Low: {today.air_temp_high}°/{today.air_temp_low}°")
        >>> print(f"Rain chance: {today.precip_probability}%")
        >>>
        >>> # Next few hours
        >>> for hour in forecast.forecast.hourly[:6]:
        >>>     time = datetime.fromtimestamp(hour.time)
        >>>     print(f"{time.strftime('%H:%M')}: {hour.air_temperature}°")

    Note:
        All measurements are returned in the units configured for your station.
        Check the 'units' field in the response to understand the unit system
        (e.g., Celsius vs Fahrenheit, m/s vs mph for wind speed).
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
        int, Field(description="The ID of the station to get observations for", gt=0)
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
    """Get the most recent weather observations from a station.

    This function retrieves detailed current weather conditions including:
    - Temperature, humidity, pressure
    - Wind speed and direction
    - Precipitation data
    - Solar radiation and UV index
    - Lightning detection data (if available)

    The data is returned in the units configured for the station. Check the
    'station_units' field in the response to understand the unit system.

    Args:
        station_id: The numeric ID of the weather station
        use_cache: Whether to use cached data (recommended for frequent requests)

    Returns:
        ObservationResponse containing current weather conditions and metadata

    Raises:
        ToolError: If the station is not accessible or API request fails

    Example:
        >>> obs = await get_observation(station_id=12345)
        >>> temp = obs.obs[0]["air_temperature"]  # Current temperature
        >>> units = obs.station_units["units_temp"]  # 'c' or 'f'
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
        int,
        Field(description="The ID of the station to get station information for", gt=0),
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
        int, Field(description="The ID of the station to get forecast for", gt=0)
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
        int, Field(description="The ID of the station to get observations for", gt=0)
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
