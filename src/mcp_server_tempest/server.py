import os
from typing import Annotated, Any, Dict

from cachetools import TTLCache
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from .models import (
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
    # tags={"weather", "sensors", "tempest"},
    # dependencies=["cachetools", "pydantic", "fastmcp", "weatherflow4py"],
)


def _get_api_token(env_var: str = "WEATHERFLOW_API_TOKEN") -> str:
    if not (token := os.getenv(env_var)):
        raise ToolError(
            f"No Tempest API token found. This should be configured using the `{env_var}` environment variable."
        )
    return token


async def _get_stations_data(ctx: Context, use_cache: bool = True) -> Dict[str, Any]:
    """Shared logic for getting stations data."""
    token = _get_api_token()

    if use_cache and "stations" in cache:
        await ctx.info("Using cached station data")
        return cache["stations"]

    await ctx.info("Getting stations via the Tempest API")
    result = await api_get_stations(token)
    cache["stations"] = result
    return result


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
) -> Dict[str, Any]:
    """
    Retrieve a list of the weather stations that the user has access to.

    Get station metadata and metadata for the Devices in it. Each user
    can create multiple Stations. A Device can only be in one Station at a
    time. Only devices with a serial_number value can submit new observations.
    A Device wihout a serial_number indicates that Device is no longer active.

    Parameters:
        use_cache: Whether to use the cache to store the results of the request
          (default: True). Typically, stations do not change frequently, so this
          is a good way to avoid making unnecessary API calls.

    Returns:
        dict: A dictionary containing station data and API status with the following structure:

        stations : list of dict
            Array of weather station objects, each containing:

            station_id : int
                Unique identifier for the weather station

            name : str
                Internal name of the weather station (e.g., "Seattle")

            public_name : str
                Public display name of the station (e.g., "Fairview Ave E")

            latitude : float
                Latitude coordinate of the station

            longitude : float
                Longitude coordinate of the station

            timezone : str
                IANA timezone identifier (e.g., "America/Los_Angeles")

            timezone_offset_minutes : int
                UTC offset in minutes (negative for west of UTC)

            created_epoch : int
                Unix timestamp when the station was created

            last_modified_epoch : int
                Unix timestamp of last station modification

            is_local_mode : bool
                Whether the station is operating in local mode

            station_meta : dict
                Station metadata containing:
                - elevation (float): Station elevation in meters above sea level
                - share_with_wf (bool): Whether data is shared with WeatherFlow
                - share_with_wu (bool): Whether data is shared with Weather Underground

            devices : list of dict
                Array of devices connected to the station, each containing:
                - device_id (int): Unique device identifier
                - device_type (str): Type of device ('ST' for outdoor sensor, 'HB' for hub)
                - serial_number (str): Device serial number
                - firmware_revision (str): Current firmware version
                - hardware_revision (str): Hardware revision number
                - device_meta (dict): Device-specific metadata:
                    - agl (float): Height above ground level in meters
                    - environment (str): Installation environment ('indoor', 'outdoor')
                    - name (str): Device name/serial number
                    - wifi_network_name (str): Connected WiFi network name
                - device_settings (dict or None): Device-specific configuration settings
                    - show_precip_final (bool): Whether to show final precipitation values

            station_items : list of dict
                Configuration of station measurement items, each containing:
                - item (str): Type of measurement ('air_temperature_humidity', 'barometric_pressure', etc.)
                - station_id (int): Associated station ID
                - station_item_id (int): Unique item identifier
                - location_id (int): Location identifier
                - location_item_id (int): Location-specific item identifier
                - device_id (int): Device providing this measurement
                - sort (int or None): Display sort order

            capabilities : None or dict
                Station capabilities (currently null in this implementation)

        status : dict
            API response status information:
            - status_code (int): Response status code (0 = SUCCESS)
            - status_message (str): Status message description

    Notes
    -----
    - Device types: 'ST' = Tempest outdoor sensor, 'HB' = Hub
    - AGL (Above Ground Level) measurements are in meters
    - Elevation is in meters above sea level
    - All timestamps are Unix epoch time (seconds since 1970-01-01 UTC)
    - Station items represent the configured measurements for the station
    - Device settings may be None if no custom settings are configured
    - Multiple stations may be returned if the user has access to more than one
    """

    try:
        data = await _get_stations_data(ctx, use_cache)
        ctx.info(f"Using pydantic stuff!")
        return StationsResponse(**data)
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
) -> Dict[str, Any]:
    """Get information about a specific weather station

    Parameters:
        station_id: The station ID to get information for
        use_cache: Whether to use the cache to store the results of the request (default: True).
          Station configurations do not typicallychange frequently, so this is a good way to avoid
          making unnecessary API calls.

    Returns:
        A dictionary containing comprehensive station metadata and device information with the following structure:

        station_id : int
            Unique identifier for the weather station

        name : str
            Internal name of the weather station (e.g., "Seattle")

        public_name : str
            Public display name of the station (e.g., "Lake Union")

        latitude : float
            Latitude coordinate of the station

        longitude : float
            Longitude coordinate of the station

        timezone : str
            IANA timezone identifier (e.g., "America/Los_Angeles")

        timezone_offset_minutes : int
            UTC offset in minutes (negative for west of UTC)

        created_epoch : int
            Unix timestamp when the station was created

        last_modified_epoch : int
            Unix timestamp of last station modification

        is_local_mode : bool
            Whether the station is operating in local mode

        station_meta : dict
            Station metadata containing:
            - elevation (float): Station elevation in meters above sea level
            - share_with_wf (bool): Whether data is shared with WeatherFlow
            - share_with_wu (bool): Whether data is shared with Weather Underground

        devices : list of dict
            Array of devices connected to the station, each containing:
            - device_id (int): Unique device identifier
            - device_type (str): Type of device ('ST' for outdoor sensor, 'HB' for hub)
            - serial_number (str): Device serial number
            - firmware_revision (str): Current firmware version
            - hardware_revision (str): Hardware revision number
            - device_meta (dict): Device-specific metadata:
                - agl (float): Height above ground level in meters
                - environment (str): Installation environment ('indoor', 'outdoor')
                - name (str): Device name/serial number
                - wifi_network_name (str): Connected WiFi network name
            - device_settings (dict or None): Device-specific configuration settings
                - show_precip_final (bool): Whether to show final precipitation values

        station_items : list of dict
            Configuration of station measurement items, each containing:
            - item (str): Type of measurement ('air_temperature_humidity', 'barometric_pressure', etc.)
            - station_id (int): Associated station ID
            - station_item_id (int): Unique item identifier
            - location_id (int): Location identifier
            - location_item_id (int): Location-specific item identifier
            - device_id (int): Device providing this measurement
            - sort (int or None): Display sort order

        capabilities : list of dict
            Station measurement capabilities, each containing:
            - capability (str): Measurement capability type
            - device_id (int): Device providing this capability
            - environment (str): Operating environment ('indoor', 'outdoor')
            - agl (float or None): Height above ground level in meters
            - show_precip_final (bool or None): Precipitation display setting

    Notes
    -----
    - Device types: 'ST' = Tempest outdoor sensor, 'HB' = Hub
    - AGL (Above Ground Level) measurements are in meters
    - Elevation is in meters above sea level
    - All timestamps are Unix epoch time (seconds since 1970-01-01 UTC)
    - Station items represent the configured measurements for the station
    - Capabilities show what measurements each device can provide
    - Device settings may be None if no custom settings are configured
    """
    token = _get_api_token()

    cache_id = f"station_id_{station_id}"

    if use_cache and cache_id in cache:
        await ctx.info(f"Using cached station data for station {station_id}")
        return cache[cache_id]

    try:
        await ctx.info(
            f"Getting information for station {station_id} via the Tempest API"
        )
        result = await api_get_station_id(station_id, token)
        cache[cache_id] = result
        return result
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
        int, Field(description="The ID of the station to get information for")
    ],
    use_cache: Annotated[
        bool,
        Field(
            default=True,
            description="Whether to use the cache to store the results of the request (default: True)",
        ),
    ],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Get the forecast and current conditions for a specific weather station

    Parameters:
        station_id: The ID of the station to get information for
        use_cache: Whether to use the cache to store the results of the request (default: True)

    This tool resturns a dictionary containing weather forecast and current
    conditions data with the following structure:

    forecast : dict
        Contains daily and hourly forecast arrays

        daily : list of dict
            10-day daily forecast with each day containing:
            - air_temp_high/low (float): High/low temperatures in Celsius
            - day_num (int): Day of month (1-31)
            - day_start_local (int): Unix timestamp for start of day in local time
            - month_num (int): Month number (1-12)
            - icon (str): Weather icon identifier ('clear-day', 'partly-cloudy-day', etc.)
            - conditions (str): Weather conditions description ('Clear', 'Partly Cloudy', etc.)
            - precip_probability (int): Precipitation probability (0-100)
            - precip_type (str): Type of precipitation ('rain', 'snow', etc.)
            - precip_icon (str): Precipitation icon identifier
            - sunrise/sunset (int): Unix timestamps for sunrise/sunset

        hourly : list of dict
            Detailed hourly forecast (typically 240+ hours) with each hour containing:
            - air_temperature (float): Temperature in Celsius
            - local_day/hour (int): Local day and hour
            - time (int): Unix timestamp
            - precip (float): Precipitation amount in mm
            - precip_probability (int): Precipitation probability (0-100)
            - precip_type (str): Type of precipitation
            - relative_humidity (int): Relative humidity percentage (0-100)
            - sea_level_pressure (float): Atmospheric pressure in mb
            - wind_avg (float): Average wind speed in m/s
            - wind_direction (float): Wind direction in degrees (0-360)
            - wind_direction_cardinal (str): Cardinal wind direction ('N', 'NE', etc.)
            - wind_gust (float): Wind gust speed in m/s
            - conditions (str): Weather conditions description
            - icon (str): Weather icon identifier
            - feels_like (float): Apparent temperature in Celsius
            - uv (float): UV index

    current_conditions : dict
        Real-time weather observations including:
        - air_temperature (float): Current temperature in Celsius
        - conditions (str): Current weather conditions
        - feels_like (float): Apparent temperature in Celsius
        - icon (str): Current weather icon
        - relative_humidity (int): Current humidity percentage
        - sea_level_pressure (float): Current pressure in mb
        - wind_avg/gust (float): Wind speeds in m/s
        - wind_direction (float): Wind direction in degrees
        - wind_direction_cardinal (str): Cardinal wind direction
        - uv (int): Current UV index
        - time (int): Unix timestamp of observation
        - Additional measurements: solar_radiation, brightness, dew_point,
            wet_bulb_temperature, lightning data, precipitation accumulations

    location_name : str
        Name of the weather station location (e.g., "Seattle")

    latitude : float
        Latitude coordinate of the station

    longitude : float
        Longitude coordinate of the station

    timezone : str
        IANA timezone identifier (e.g., "America/Los_Angeles")

    timezone_offset_minutes : int
        UTC offset in minutes (negative for west of UTC)

    units : dict
        Unit specifications for all measurements:
        - units_temp (str): Temperature units ('c' for Celsius)
        - units_wind (str): Wind speed units ('mps' for meters per second)
        - units_pressure (str): Pressure units ('mb' for millibars)
        - units_precip (str): Precipitation units ('mm' for millimeters)
        - units_distance (str): Distance units ('km' for kilometers)
        - units_other (str): General unit system ('metric')
    """
    token = _get_api_token()

    cache_id = f"forecast_{station_id}"
    if use_cache and cache_id in cache:
        await ctx.info(f"Using cached forecast data for station {station_id}")
        return cache[cache_id]

    try:
        await ctx.info(f"Getting forecast for station {station_id} via the Tempest API")
        result = await api_get_forecast(station_id, token)
        cache[cache_id] = result
        return result
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
        int, Field(description="The ID of the station to get information for")
    ],
    use_cache: Annotated[
        bool,
        Field(
            default=True,
            description="Whether to use the cache to store the results of the request (default: True)",
        ),
    ],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Get recent detailed observations for a specific weather station

    Observations contain the most recent weather conditions at the given station.

    Parameters:
        station_id: The ID of the station to get information for
        use_cache: Whether to use the cache to store the results of the request (default: True)

    Returns:
        A dictionary containing current weather observations and station metadata with the following structure:

    outdoor_keys : list of str
        List of available outdoor measurement field names, described below

    obs : list of dict
        Array of observation records (typically contains one current observation) with each record containing:
        - timestamp (int): Unix timestamp of the observation
        - air_temperature (float): Current air temperature
        - barometric_pressure (float): Station barometric pressure
        - station_pressure (float): Station-level atmospheric pressure
        - pressure_trend (str): Pressure trend ('steady', 'rising', 'falling')
        - sea_level_pressure (float): Sea level adjusted atmospheric pressure
        - relative_humidity (int): Relative humidity percentage (0-100)
        - precip (float): Current precipitation rate
        - precip_accum_last_1hr (float): Precipitation accumulation in last hour
        - precip_accum_local_day (float): Precipitation accumulation for current local day
        - precip_accum_local_day_final (float): Final precipitation total for current day
        - precip_accum_local_yesterday (float): Precipitation accumulation for yesterday
        - precip_accum_local_yesterday_final (float): Final precipitation total for yesterday
        - precip_analysis_type_yesterday (int): Type of precipitation analysis for yesterday
        - precip_minutes_local_day (int): Minutes of precipitation today
        - precip_minutes_local_yesterday (int): Minutes of precipitation yesterday
        - precip_minutes_local_yesterday_final (int): Final minutes of precipitation yesterday
        - wind_avg (float): Average wind speed
        - wind_direction (int): Wind direction in degrees (0-360)
        - wind_gust (float): Wind gust speed
        - wind_lull (float): Wind lull (minimum wind speed)
        - solar_radiation (float): Solar radiation intensity
        - uv (float): UV index
        - brightness (float): Light intensity in lux
        - lightning_strike_last_epoch (int): Unix timestamp of last lightning strike
        - lightning_strike_last_distance (int): Distance to last lightning strike
        - lightning_strike_count (int): Current lightning strike count
        - lightning_strike_count_last_1hr (int): Lightning strikes in last hour
        - lightning_strike_count_last_3hr (int): Lightning strikes in last 3 hours
        - feels_like (float): Apparent temperature (heat index or wind chill)
        - heat_index (float): Heat index temperature
        - wind_chill (float): Wind chill temperature
        - dew_point (float): Dew point temperature
        - wet_bulb_temperature (float): Wet bulb temperature
        - wet_bulb_globe_temperature (float): Wet bulb globe temperature
        - delta_t (float): Delta T (difference between air temp and wet bulb temp)
        - air_density (float): Air density

    station_id : int
        Unique identifier for the weather station

    station_name : str
        Name of the weather station (e.g., "Seattle")

    public_name : str
        Public display name of the station (e.g., "Lake Union")

    latitude : float
        Latitude coordinate of the station

    longitude : float
        Longitude coordinate of the station

    elevation : float
        Elevation of the station in meters

    is_public : bool
        Whether the station data is publicly accessible

    timezone : str
        IANA timezone identifier (e.g., "America/Los_Angeles")

    station_units : dict
        Unit specifications for all measurements:
        - units_temp (str): Temperature units ('f' for Fahrenheit, 'c' for Celsius)
        - units_wind (str): Wind speed units ('mph', 'mps', 'kph')
        - units_precip (str): Precipitation units ('in' for inches, 'mm' for millimeters)
        - units_pressure (str): Pressure units ('inhg', 'mb', 'hpa')
        - units_distance (str): Distance units ('mi' for miles, 'km' for kilometers)
        - units_direction (str): Direction format ('cardinal', 'degrees')
        - units_other (str): General unit system ('imperial', 'metric')

    status : dict
        API response status information:
        - status_code (int): Response status code (0 = SUCCESS)
        - status_message (str): Status message description

    """
    token = _get_api_token()

    cache_id = f"observation_{station_id}"
    if use_cache and cache_id in cache:
        await ctx.info(f"Using cached observation data for station {station_id}")
        return cache[cache_id]

    try:
        await ctx.info(
            f"Getting observations for station {station_id} via the Tempest API"
        )
        result = await api_get_observation(station_id, token)
        cache[cache_id] = result
        return result
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.resource(
    uri="weather://tempest/stations",
    name="Get Weather Stations",
    mime_type="application/json",
)
async def get_stations_resource(ctx: Context = None) -> Dict[str, Any]:
    """Get a list of all your WeatherFlow stations.

    This resource can be used to get a list of all of the configured weather stations that the user has access to, along with all connected devices.
    Each result contains information about the station, including its name, location, devices, state, and more.
    A Device wihout a serial_number indicates that Device is no longer active.
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
        int, Field(description="The ID of the station to get information for")
    ],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Get information and devices for a specific weather station

    This resource can be used to get a list of all of the configured weather stations that the user has access to, along with all connected devices.
    Each result contains information about the station, including its name, location, devices, state, and more.
    A Device wihout a serial_number indicates that Device is no longer active.

    Args:
        station_id: The ID of the station to get information for
    """

    token = _get_api_token()

    cache_id = f"station_id_{station_id}"
    if cache_id in cache:
        await ctx.info(f"Using cached station data for station {station_id}")
        return cache[cache_id]

    try:
        await ctx.info(
            f"Getting information for station {station_id} via the Tempest API"
        )
        result = await api_get_station_id(station_id, token)
        cache[cache_id] = result
        return result
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.resource(
    uri="weather://tempest/forecast/{station_id}",
    name="GetWeatherForecast",
    mime_type="application/json",
)
async def get_forecast_resource(
    station_id: Annotated[
        int, Field(description="The ID of the station to get information for")
    ],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Get information and devices for a specific weather station

    This resource allows the user to retrieve the weather forecast from the specified weather station.

    Args:
        station_id: The ID of the station to get information for
    """

    token = _get_api_token()

    cache_id = f"forecast_{station_id}"
    if cache_id in cache:
        await ctx.info(f"Using cached forecast data for station {station_id}")
        return cache[cache_id]

    try:
        await ctx.info(f"Getting forecast for station {station_id} via the Tempest API")
        result = await api_get_forecast(station_id, token)
        cache[cache_id] = result
        return result
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.resource(
    uri="weather://tempest/observations/{station_id}",
    name="GetWeatherObservations",
    mime_type="application/json",
)
async def get_observation_resource(
    station_id: Annotated[
        int, Field(description="The ID of the station to get information for")
    ],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Get latest detailed observations for a specific weather station

    This resource allows the user to retrieve the weather forecast from the specified weather station.
    """

    token = _get_api_token()

    await ctx.info(f"Getting observations for station {station_id}...")

    try:
        result = await api_get_observation(station_id, token)
        return result
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


if __name__ == "__main__":
    mcp.run()
