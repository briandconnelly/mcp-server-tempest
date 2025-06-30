from .server import (
    get_api_help,
    get_better_forecast,
    get_station_observations,
    get_station_summary,
    get_stations_by_device_id,
    get_unit_options,
    mcp,
)

__all__ = [
    "get_api_help",
    "get_better_forecast",
    "get_station_observations",
    "get_station_summary",
    "get_stations_by_device_id",
    "get_unit_options",
]


def main():
    mcp.run()


if __name__ == "__main__":
    main()
