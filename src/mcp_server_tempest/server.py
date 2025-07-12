import os
from typing import Annotated, Any, Dict

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from .rest import api_get_stations, api_get_station_id, api_get_forecast

_notoken_message = "No API token found. This should be configured using the `WEATHERFLOW_API_TOKEN` environment variable."


# Create the MCP server
mcp = FastMCP(name="WeatherFlow Tempest API Server")


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
        result = await api_get_stations(token)
        return result
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.tool()
async def get_station_id(
    station_id: Annotated[
        int, Field(description="The station ID to get information for")
    ],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Get information about a specific weather station"""
    if not (token := os.getenv("WEATHERFLOW_API_TOKEN")):
        raise ToolError(_notoken_message)

    await ctx.info(f"Getting information for station {station_id}...")

    try:
        result = await api_get_station_id(station_id, token)
        return result
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.tool()
async def get_forecast(
    station_id: Annotated[
        int, Field(description="The ID of the station to get information for")
    ],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Get the forecast for a specific weather station"""
    if not (token := os.getenv("WEATHERFLOW_API_TOKEN")):
        raise ToolError(_notoken_message)

    await ctx.info(f"Getting forecast for station {station_id}...")

    try:
        result = await api_get_forecast(station_id, token)
        return result
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.resource(
    uri="tempest://stations",
    name="GetWeatherStations",
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
        result = await api_get_stations(token)
        return result
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.resource(
    uri="tempest://stations/{station_id}",
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
        result = await api_get_station_id(station_id, token)
        return result
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


@mcp.resource(
    uri="tempest://forecast/{station_id}",
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

    This resource can be used to get a list of all of the configured weather stations along with all connected devices.
    Each result contains information about the station, including its name, location, devices, state, and more.
    A Device wihout a serial_number indicates that Device is no longer active.

    Args:
        station_id: The ID of the station to get information for
    """

    if not (token := os.getenv("WEATHERFLOW_API_TOKEN")):
        raise ToolError(_notoken_message)

    await ctx.info(f"Getting forecast for station {station_id}...")

    try:
        result = await api_get_forecast(station_id, token)
        return result
    except Exception as e:
        raise ToolError(f"Request failed: {str(e)}")


if __name__ == "__main__":
    mcp.run()
