from .rest import (
    api_get_stations,
    api_get_station_id,
    api_get_forecast,
    api_get_observation,
)
from .server import (
    get_stations,
    get_station_id,
    get_stations_resource,
    get_station_id_resource,
    get_forecast,
    get_forecast_resource,
    mcp,
)


__all__ = [
    "get_stations",
    "get_station_id",
    "get_stations_resource",
    "get_station_id_resource",
    "api_get_stations",
    "api_get_station_id",
    "api_get_forecast",
    "get_forecast",
    "get_forecast_resource",
    "api_get_observation",
]


def main():
    mcp.run()


if __name__ == "__main__":
    main()
