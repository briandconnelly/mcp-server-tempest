# WeatherFlow Tempest MCP Server

A Model Context Protocol (MCP) server that provides seamless access to WeatherFlow Tempest weather station data.
This server enables AI assistants and applications to retrieve real-time weather observations, forecasts, and station metadata.


## 🌤️ Features

- **Real-time Weather Data**: Access current conditions from personal weather stations
- **Weather Forecasts**: Get hourly and daily forecasts with professional meteorological models
- **Station Management**: Discover and manage multiple weather stations
- **Device Information**: Detailed metadata about connected weather devices
- **Intelligent Caching**: Automatic caching with configurable TTL for optimal performance
- **Multiple Access Methods**: Both tools (interactive queries) and resources (data access)
- **Comprehensive Data**: Temperature, humidity, pressure, wind, precipitation, solar radiation, UV index, and lightning detection


## 🚀 Quick Start

### Prerequisites

- Python 3.13 or higher
- WeatherFlow API token (get one at [tempestwx.com/settings/tokens](https://tempestwx.com/settings/tokens))

### Installation

While each client has its own way of specifying, you'll generally use the following values:

| Field | Value |
|-------|-------|
| **Command** | `uvx` |
| **Arguments** | `mcp-server-tempest` |
| **Environment** | `WEATHERFLOW_API_TOKEN` = `<YOUR TOKEN>` |


### Development Version

If you'd like to use the latest and greatest, the server can be pulled straight from GitHub.
Just add an additional `--from` argument:


| Field | Value |
|-------|-------|
| **Command** | `uvx` |
| **Arguments** | `--from`, `git+https://github.com/briandconnelly/mcp-server-tempest`, `mcp-server-tempest` |
| **Environment** | `WEATHERFLOW_API_TOKEN` = `<YOUR TOKEN>` |


## 📋 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `WEATHERFLOW_API_TOKEN` | Your WeatherFlow API token | - | ✅ Yes |
| `WEATHERFLOW_CACHE_TTL` | Cache timeout in seconds | 300 | No |
| `WEATHERFLOW_CACHE_SIZE` | Maximum cache entries | 100 | No |


## 🛠️ Usage

### Available Tools

#### `get_stations()`
Get a list of all your weather stations and connected devices.

```python
# Get all available stations
stations = await client.call_tool("get_stations")
for station in stations.stations:
    print(f"Station: {station.name} (ID: {station.station_id})")
    print(f"Location: {station.latitude}, {station.longitude}")
```

#### `get_observation(station_id)`
Get current weather conditions for a specific station.

```python
# Get current conditions
obs = await client.call_tool("get_observation", {"station_id": 12345})
current = obs.obs[0]
print(f"Temperature: {current.air_temperature}°")
print(f"Humidity: {current.relative_humidity}%")
print(f"Wind: {current.wind_avg} {obs.station_units.units_wind}")
```

#### `get_forecast(station_id)`
Get weather forecast and current conditions.

```python
# Get forecast
forecast = await client.call_tool("get_forecast", {"station_id": 12345})

# Current conditions
current = forecast.current_conditions
print(f"Current: {current.air_temperature}°")
print(f"Conditions: {current.conditions}")

# Today's forecast
today = forecast.forecast.daily[0]
print(f"High/Low: {today.air_temp_high}°/{today.air_temp_low}°")
print(f"Rain chance: {today.precip_probability}%")
```

#### `get_station_id(station_id)`
Get detailed information about a specific station.

```python
# Get station details
station = await client.call_tool("get_station_id", {"station_id": 12345})
print(f"Station: {station.name}")
print(f"Elevation: {station.station_meta.elevation}m")
print(f"Devices: {len(station.devices)}")
```

#### `clear_cache()`
Clear the data cache (useful for testing).

```python
# Clear cache
await client.call_tool("clear_cache")
```

### Available Resources

The server also provides resources for data access:

- `weather://tempest/stations` - List all stations
- `weather://tempest/stations/{station_id}` - Station details
- `weather://tempest/observations/{station_id}` - Current observations
- `weather://tempest/forecast/{station_id}` - Weather forecast


## 🌟 Examples

### Basic Weather Check

```python
# Get your stations
stations = await client.call_tool("get_stations")
station_id = stations.stations[0].station_id

# Get current conditions
obs = await client.call_tool("get_observation", {"station_id": station_id})
current = obs.obs[0]

print(f"🌡️  Temperature: {current.air_temperature}°{obs.station_units.units_temp}")
print(f"💧 Humidity: {current.relative_humidity}%")
print(f"💨 Wind: {current.wind_avg} {obs.station_units.units_wind}")
print(f"🌧️  Precipitation: {current.precip_accum_local_day} {obs.station_units.units_precip}")
```

### Weather Forecast

```python
# Get forecast
forecast = await client.call_tool("get_forecast", {"station_id": station_id})

# Today's weather
today = forecast.forecast.daily[0]
print(f"📅 Today: {today.conditions}")
print(f"🌡️  High: {today.air_temp_high}° / Low: {today.air_temp_low}°")
print(f"🌧️  Rain chance: {today.precip_probability}%")

# Next few hours
for hour in forecast.forecast.hourly[:6]:
    time = datetime.fromtimestamp(hour.time)
    print(f"🕐 {time.strftime('%H:%M')}: {hour.air_temperature}° - {hour.conditions}")
```

### Station Information

```python
# Get station details
station = await client.call_tool("get_station_id", {"station_id": station_id})

print(f"🏠 Station: {station.name}")
print(f"📍 Location: {station.latitude}°, {station.longitude}°")
print(f"⛰️  Elevation: {station.station_meta.elevation}m")
print(f"🕐 Timezone: {station.timezone}")

# Check device status
for device in station.devices:
    if device.serial_number:
        status = "🟢 Online" if device.device_meta else "🔴 Offline"
        print(f"📡 {device.device_type}: {status}")
```


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [WeatherFlow](https://weatherflow.com/) for providing the Tempest weather station and API
- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP specification
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP server framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/mcp-server-tempest/issues)
- **Documentation**: [WeatherFlow API Docs](https://weatherflow.github.io/Tempest/api/)
- **Community**: [WeatherFlow Community](https://community.weatherflow.com/)
