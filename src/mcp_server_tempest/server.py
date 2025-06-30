import os
from typing import Annotated, Any, Dict, List, Optional

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

# Create the MCP server
mcp = FastMCP(name="WeatherFlow Tempest API Server")

# Base URL for the WeatherFlow API
BASE_URL = "https://swd.weatherflow.com/swd/rest"

# Create HTTP client
client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


@mcp.tool
async def get_better_forecast(
    station_id: int,
    units_temp: Annotated[str, Field(description="Temperature units")] = "f",
    units_wind: Annotated[str, Field(description="Wind speed units")] = "mph",
    units_pressure: Annotated[str, Field(description="Pressure units")] = "inhg",
    units_precip: Annotated[str, Field(description="Precipitation units")] = "in",
    units_distance: Annotated[
        str, Field(description="Distance/visibility units")
    ] = "mi",
) -> Dict[str, Any]:
    """
    Get detailed weather forecast for a specific WeatherFlow station.

    Args:
        station_id: The station ID to get forecast for
        token: Your WeatherFlow API token
        units_temp: Temperature units (c, f, k)
        units_wind: Wind speed units (mps, mph, kph, kts)
        units_pressure: Pressure units (mb, inhg, mmhg)
        units_precip: Precipitation units (mm, in)
        units_distance: Distance units (km, mi)
    """

    token = os.getenv("WEATHERFLOW_API_TOKEN")

    if not token:
        raise ToolError("No API token found")

    try:
        params = {
            "station_id": station_id,
            "token": token,
            "units_temp": units_temp,
            "units_wind": units_wind,
            "units_pressure": units_pressure,
            "units_precip": units_precip,
            "units_distance": units_distance,
        }

        response = await client.get("/better_forecast", params=params)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


@mcp.tool
async def get_station_observations(
    device_id: int,
    time_start: Optional[int] = None,
    time_end: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Get current and recent observations from a WeatherFlow station.
    A station has one or more devices, which are identified by device_id.
    A user's station_id and device_idvalues can be determined by calling get_stations().

    Not all devices are weather sensors.
    Weather devices can be identified by `device_type` (station is "ST"), will typically
    be labeled as "outdoor" in the device_meta metadata, and will provide
    weather-related measurements.

    A user may or not be geographically located near a station.
    If the user asks for a weather forecast without specifying that the station
    should be used, first determine the location of the user. This information can
    be used to determine whether or not they are near the weather station.
    If there is some ambiguity about the user's location, you can include information about the weather station's location or ask the user if they would like to retrieve information from their weather station.

    If memory is available, remember current observations so that they can be compared against past and future observations to detect and interpret trends.
    Args:
        station_id: The station ID to get observations from
        token: Your WeatherFlow API token
        time_start: Start time for historical data (Unix timestamp)
        time_end: End time for historical data (Unix timestamp)
    """

    token = os.getenv("WEATHERFLOW_API_TOKEN")

    if not token:
        raise ToolError("No API token found")

    try:
        params = {"device_id": device_id, "token": token}

        if time_start:
            params["time_start"] = time_start
        if time_end:
            params["time_end"] = time_end

        response = await client.get(f"/observations/device/{device_id}", params=params)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


@mcp.tool
async def get_stations_by_device_id(device_id: List[int]) -> Dict[str, Any]:
    """
    Get station information by device IDs.
    A user's station_id values can be determined by calling get_stations().

    Args:
        device_id: List of device IDs to look up
    """

    token = os.getenv("WEATHERFLOW_API_TOKEN")

    if not token:
        raise ToolError("No API token found")

    try:
        # Convert list to comma-separated string
        device_ids_str = ",".join(map(str, device_id))

        params = {"device_id": device_ids_str, "token": token}

        response = await client.get("/stations", params=params)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


@mcp.tool
async def get_stations() -> Dict[str, Any]:
    """
    Retrieve a list of your stations along with all connected devices
    Get station metadata and metadata for the Devices in it. Each user
    can create multiple Stations. A Device can only be in one Station at a
    time. Only devices with a serial_number value can send new observations.
    A Device wihout a serial_number indicates that Device is no longer active.
    """

    token = os.getenv("WEATHERFLOW_API_TOKEN")

    if not token:
        raise ToolError("No API token found")

    try:
        params = {"token": token}

        response = await client.get("/stations/", params=params)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


@mcp.tool
async def get_station_metadata(station_id: int) -> Dict[str, Any]:
    """
    Get detailed metadata for a specific station including location and device info.
    A user's station_id values can be determined by calling get_stations().

    Args:
        station_id: The station ID to get metadata for
    """

    token = os.getenv("WEATHERFLOW_API_TOKEN")

    if not token:
        raise ToolError("No API token found")

    try:
        params = {"station_id": station_id, "token": token}

        response = await client.get(f"/stations/{station_id}", params=params)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


# Resource to provide API documentation and help
@mcp.resource("tempest://api/help")
def get_api_help() -> str:
    """Provides information about using the WeatherFlow Tempest API."""
    return """
WeatherFlow Tempest API MCP Server

This server provides access to WeatherFlow's remoteweather data through
the following tools:

1. get_better_forecast: Get detailed weather forecast
   - Requires: station_id
   - Optional: unit preferences for temperature, wind, pressure, etc.

2. get_station_observations: Get current/recent weather observations
   - Requires: device_id
   - Optional: time_start, time_end for historical data

3. get_stations_by_device_id: Find stations by device IDs
   - Requires: device_id (list)

4. get_station_metadata: Get station details and location info
   - Requires: station_id

API Token: You need a WeatherFlow API token to use these tools.
Visit: https://weatherflow.github.io/Tempest/api/ for more information.

Unit Options:
- Temperature: c (Celsius), f (Fahrenheit), k (Kelvin)
- Wind: mps (m/s), mph (miles/hour), kph (km/hour), kts (knots)
- Pressure: mb (millibars), inhg (inches Hg), mmhg (mmHg)
- Precipitation: mm (millimeters), in (inches)
- Distance: km (kilometers), mi (miles)
"""


@mcp.resource("tempest://config/units")
def get_unit_options() -> Dict[str, List[str]]:
    """Available unit options for the WeatherFlow API."""
    return {
        "temperature": ["c", "f", "k"],
        "wind": ["mps", "mph", "kph", "kts"],
        "pressure": ["mb", "inhg", "mmhg"],
        "precipitation": ["mm", "in"],
        "distance": ["km", "mi"],
    }


# Example usage resource
@mcp.resource("tempest://examples/forecast")
def get_forecast_example() -> str:
    """Example of how to get a weather forecast."""
    return """
Example: Getting a Weather Forecast

To get a forecast for a station, you'll need:
1. A station_id (find this from your WeatherFlow account or device). You can also get this by calling get_stations().

Example call:
get_better_forecast(
    station_id=12345,
    units_temp="f",
    units_wind="mph"
)

This will return detailed forecast data including:
- Current conditions
- Hourly forecast
- Daily forecast
- Weather alerts
- Station metadata
"""


if __name__ == "__main__":
    mcp.run()
