from .server import (
    get_better_forecast,
    get_stations_by_device_id,
    get_station_observations,
    get_station_metadata,
    get_api_help,
    get_unit_options,
    mcp,
)

__all__ = [
    "get_better_forecast",
    "get_stations_by_device_id",
    "get_station_observations",
    "get_station_metadata",
    "get_api_help",
    "get_unit_options",
    "get_unit_options_by_device_id",
    "get_unit_options_by_device_id_and_station_id",
    "get_unit_options_by_device_id_and_station_id_and_variable_id",
]


def main():
    mcp.run()


if __name__ == "__main__":
    main()
