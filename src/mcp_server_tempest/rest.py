from weatherflow4py.api import WeatherFlowRestAPI


async def api_get_stations(token: str) -> dict:
    async with WeatherFlowRestAPI(token) as api:
        stations = await api.async_get_stations()
        return stations.to_dict()


async def api_get_station_id(station_id: int, token: str) -> dict:
    async with WeatherFlowRestAPI(token) as api:
        station = await api.async_get_station(station_id=station_id)
        return station[0].to_dict()


async def api_get_forecast(station_id: int, token: str) -> dict:
    async with WeatherFlowRestAPI(token) as api:
        forecast = await api.async_get_forecast(station_id=station_id)
        return forecast.to_dict()


async def api_get_observation(station_id: int, token: str) -> dict:
    async with WeatherFlowRestAPI(token) as api:
        observation = await api.async_get_observation(station_id=station_id)
        return observation.to_dict()
