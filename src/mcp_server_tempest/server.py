import os
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional, Literal

import httpx
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

_notoken_message = "No API token found. This should be configured using the `WEATHERFLOW_API_TOKEN` environment variable."


# Create the MCP server
mcp = FastMCP(name="WeatherFlow Tempest API Server")

# Base URL for the WeatherFlow API
BASE_URL = "https://swd.weatherflow.com/swd/rest"

# Create HTTP client
client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


@mcp.tool
async def get_better_forecast(
    station_id: Annotated[
        int, Field(description="The station ID to get forecast data for", gt=0)
    ],
    units_temp: Annotated[
        Literal["c", "f", "k"], Field(description="Temperature units")
    ] = "f",
    units_wind: Annotated[
        Literal["mps", "mph", "kph", "kts"], Field(description="Wind speed units")
    ] = "mph",
    units_pressure: Annotated[
        Literal["mb", "inhg", "mmhg"], Field(description="Pressure units")
    ] = "inhg",
    units_precip: Annotated[
        Literal["mm", "in"], Field(description="Precipitation units")
    ] = "in",
    units_distance: Annotated[
        Literal["km", "mi"], Field(description="Distance/visibility units")
    ] = "mi",
    ctx: Context = None,
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

    Returns:
        A dictionary containing current conditions, daily forecast,
        and hourly forecast.
    """

    if not (token := os.getenv("WEATHERFLOW_API_TOKEN")):
        raise ToolError(_notoken_message)

    await ctx.info(f"Getting forecast for station {station_id}...")

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
        raise ToolError(f"HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.tool
async def get_station_observations(
    device_id: Annotated[
        int, Field(description="The device ID to get observations for")
    ],
    time_start: Annotated[
        Optional[int],
        Field(
            default=None, description="Start time for historical data (Unix timestamp)"
        ),
    ],
    time_end: Annotated[
        Optional[int],
        Field(
            default=None, description="End time for historical data (Unix timestamp)"
        ),
    ],
    ctx: Context = None,
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

    if not (token := os.getenv("WEATHERFLOW_API_TOKEN")):
        raise ToolError(_notoken_message)

    await ctx.info(f"Getting observations for device {device_id}...")

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
        raise ToolError(f"HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.tool
async def get_stations_by_device_id(
    device_id: Annotated[List[int], Field(description="List of device IDs to look up")],
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get station information by device IDs.
    A user's station_id values can be determined by calling get_stations().

    Args:
        device_id: List of device IDs to look up
    """

    if not (token := os.getenv("WEATHERFLOW_API_TOKEN")):
        raise ToolError(_notoken_message)

    await ctx.info("Getting stations by device ID...")

    try:
        # Convert list to comma-separated string
        device_ids_str = ",".join(map(str, device_id))

        params = {"device_id": device_ids_str, "token": token}

        response = await client.get("/stations", params=params)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        raise ToolError(f"HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.tool
async def get_stations(ctx: Context = None) -> Dict[str, Any]:
    """
    Retrieve a list of your stations along with all connected devices
    Get station metadata and metadata for the Devices in it. Each user
    can create multiple Stations. A Device can only be in one Station at a
    time. Only devices with a serial_number value can send new observations.
    A Device wihout a serial_number indicates that Device is no longer active.
    """

    if not (token := os.getenv("WEATHERFLOW_API_TOKEN")):
        raise ToolError(_notoken_message)

    await ctx.info("Getting stations...")

    try:
        params = {"token": token}
        response = await client.get("/stations/", params=params)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        raise ToolError(f"HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


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


@mcp.tool
async def get_station_summary(
    get_observations: Annotated[
        bool,
        Field(
            description="Whether to fetch current weather observations for each station. "
            "Set to False for faster response when only station metadata is needed."
        ),
    ] = True,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get a comprehensive overview of all your WeatherFlow stations including
    their metadata, devices, and device metadata. Current weather observations
    can also be included.
    Provides a dashboard-like view of all your weather monitoring equipment.

    Each user can create multiple Stations. A Device can only be in one Station at a
    time. Only devices with a serial_number value can send new observations.
    A Device wihout a serial_number indicates that Device is no longer active.

    Args:
        get_observations: If True, includes current weather conditions for each station.
                         If False, returns only station metadata and device information.
    """
    if not (token := os.getenv("WEATHERFLOW_API_TOKEN")):
        raise ToolError(_notoken_message)

    try:
        # Get all stations
        params = {"token": token}
        response = await client.get("/stations/", params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("stations"):
            return {"message": "No stations found in your account"}

        station_summary = []
        total_devices = 0
        active_devices = 0

        for station in data["stations"]:
            devices = station.get("devices", [])
            station_active_devices = [d for d in devices if d.get("serial_number")]
            station_weather_devices = [
                d for d in station_active_devices if d.get("device_type") == "ST"
            ]

            total_devices += len(devices)
            active_devices += len(station_active_devices)

            # Try to get current conditions if requested and we have weather devices
            current_conditions = None
            if get_observations and station_weather_devices:
                try:
                    device_id = station_weather_devices[0]["device_id"]
                    obs_params = {"device_id": device_id, "token": token}
                    obs_response = await client.get(
                        f"/observations/device/{device_id}", params=obs_params
                    )

                    if obs_response.status_code == 200:
                        obs_data = obs_response.json()
                        latest_obs = obs_data.get("obs", [])
                        if latest_obs:
                            last_obs = latest_obs[-1]
                            current_conditions = {
                                "temperature": last_obs[7],  # air_temperature
                                "humidity": last_obs[8],  # relative_humidity
                                "wind_speed": last_obs[2],  # wind_avg
                                "pressure": last_obs[6],  # station_pressure
                                "last_update": datetime.fromtimestamp(
                                    last_obs[0], timezone.utc
                                ).strftime("%Y-%m-%d %H:%M UTC"),
                            }
                except Exception as obs_error:
                    # Log the error but continue with other stations
                    current_conditions = {
                        "error": f"Failed to fetch observations: {str(obs_error)}"
                    }

            station_info = {
                "station_id": station["station_id"],
                "name": station.get("name", "Unnamed Station"),
                "location": {
                    "latitude": station.get("latitude"),
                    "longitude": station.get("longitude"),
                    "elevation": station.get("station_meta", {}).get("elevation"),
                },
                "devices": {
                    "total": len(devices),
                    "active": len(station_active_devices),
                    "weather_sensors": len(station_weather_devices),
                },
                "device_list": [
                    {
                        "device_id": device["device_id"],
                        "type": device.get("device_type", "Unknown"),
                        "active": bool(device.get("serial_number")),
                        "meta": device.get("device_meta", {}),
                    }
                    for device in devices
                ],
                "public": station.get("public", False),
            }

            # Only include current_conditions if observations were requested
            if get_observations:
                station_info["current_conditions"] = current_conditions

            station_summary.append(station_info)

        result = {
            "total_stations": len(data["stations"]),
            "total_devices": total_devices,
            "active_devices": active_devices,
            "stations": station_summary,
            "account_summary": {
                "has_weather_data": any(
                    s["devices"]["weather_sensors"] > 0 for s in station_summary
                ),
                "public_stations": len([s for s in station_summary if s["public"]]),
                "private_stations": len(
                    [s for s in station_summary if not s["public"]]
                ),
            },
        }

        # Add a note about observations if they weren't requested
        if not get_observations:
            result["note"] = (
                "Current weather observations not included. Set get_observations=True to include them."
            )

        return result

    except httpx.HTTPStatusError as e:
        raise ToolError(f"HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.resource(
    uri="tempest://stations",
    name="GetStations",
    mime_type="application/json",
)
async def get_stations_resource(ctx: Context = None) -> Dict[str, Any]:
    """Get a list of all your WeatherFlow stations.

    This resource can be used to get a list of all of the configured weather stations along with all connected devices.
    Each result contains information about the station, including its name, location, devices, state, and more.
    A Device wihout a serial_number indicates that Device is no longer active.
    """
    if not (token := os.getenv("WEATHERFLOW_API_TOKEN")):
        raise ToolError(_notoken_message)

    await ctx.info("Getting stations...")

    try:
        params = {"token": token}
        response = await client.get("/stations/", params=params)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        raise ToolError(f"HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.resource(
    uri="tempest://stations/{station_id}",
    name="GetStationByID",
    mime_type="application/json",
)
async def get_station_by_id_resource(
    station_id: Annotated[
        int, Field(description="The ID of the station to get information for")
    ],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Get information and devices for a specific weather station

    This resource can be used to get a list of all of the configured weather stations along with all connected devices.
    Each result contains information about the station, including its name, location, devices, state, and more.
    A Device wihout a serial_number indicates that Device is no longer active.

    Args:
        station_id: The ID of the station to get information for
    """
    if not (token := os.getenv("WEATHERFLOW_API_TOKEN")):
        raise ToolError(_notoken_message)

    await ctx.info(f"Getting station {station_id}...")

    try:
        params = {"station_id": station_id, "token": token}

        response = await client.get(f"/stations/{station_id}", params=params)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        raise ToolError(f"HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.resource(
    uri="tempest://observations/station/{station_id}",
    name="GetStationObservations",
    mime_type="application/json",
)
async def get_observations_station(
    station_id: Annotated[
        int,
        Field(
            description="The station ID to get latest weather observations for", gt=0
        ),
    ],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Get latest observations from a given weather station

    Get the latest federated observation for a Station. This observation is made
    from the latest Device observations that belong to the Station. If a user has
    multiple Devices of the same type they are able to designate one of them as
    primary. This is the one used to make the federated observation.

    A user can also designate each device as either indoor or outdoor. All indoor
    observation value fields will end with an "_indoor" suffix. Outdoor observations
    fields do not have a suffix.

    The station_units values represent the units of the Station's owner, not the units
    of the observation values in the API response.

    Args:
        station_id: The station ID to get observations for
    Returns:
        A dictionary containing current weather onditions at the given station

    """

    if not (token := os.getenv("WEATHERFLOW_API_TOKEN")):
        raise ToolError(_notoken_message)

    await ctx.info(f"Getting observations for station {station_id}...")

    try:
        params = {"station_id": station_id, "token": token}
        response = await client.get(
            f"/observations/station/{station_id}", params=params
        )
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        raise ToolError(f"HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.prompt
def ask_about_weather(ctx: Context = None) -> str:
    """Ask about the weather."""
    return """
    Please use the get_better_forecast tool to get a weather forecast.
    """


@mcp.resource(
    uri="tempest://observations/device/{device_id}",
    name="GetDeviceObservations",
    mime_type="application/json",
)
async def get_device_observations_resource(
    device_id: Annotated[
        int, Field(description="The device ID to get weather observations for", gt=0)
    ],
    #day_offset: Annotated[int, Field(default=None, description="TODO", ge=0)],
    #time_start: Annotated[int, Field(default=None, description="TODO", gt=0)],
    #time_end: Annotated[int, Field(default=None, description="TODO", gt=0)],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Get observations from a given weather device"""
    if not (token := os.getenv("WEATHERFLOW_API_TOKEN")):
        raise ToolError(_notoken_message)

    await ctx.info(f"Getting observations for device {device_id}...")

    try:
        params = {
            "device_id": device_id,
            "token": token,
            # "day_offset": day_offset,
            # "time_start": time_start,
            # "time_end": time_end,
        }
        response = await client.get(f"/observations/device/{device_id}", params=params)
        response.raise_for_status()

        # TODO: translate output from list to dict

        return response.json()

    except httpx.HTTPStatusError as e:
        raise ToolError(f"HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


if __name__ == "__main__":
    mcp.run()
