from enum import Enum

from pydantic import BaseModel, Field


# Enums for better type safety
class DeviceType(str, Enum):
    TEMPEST = "ST"  # Tempest outdoor sensor
    AIR = "AR"  # Air sensor (temperature, humidity, pressure, lightning)
    SKY = "SK"  # Sky sensor (wind, rain, solar radiation, UV)
    HUB = "HB"  # Hub


class Environment(str, Enum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"


class PressureTrend(str, Enum):
    STEADY = "steady"
    RISING = "rising"
    FALLING = "falling"


class TemperatureUnit(str, Enum):
    FAHRENHEIT = "f"
    CELSIUS = "c"


class WindUnit(str, Enum):
    MPH = "mph"
    MPS = "mps"  # meters per second
    KPH = "kph"


class PressureUnit(str, Enum):
    INHG = "inhg"  # inches of mercury
    MB = "mb"  # millibars
    HPA = "hpa"  # hectopascals


class PrecipUnit(str, Enum):
    INCHES = "in"
    MILLIMETERS = "mm"


class DistanceUnit(str, Enum):
    MILES = "mi"
    KILOMETERS = "km"


class DirectionUnit(str, Enum):
    CARDINAL = "cardinal"
    DEGREES = "degrees"


class UnitSystem(str, Enum):
    IMPERIAL = "imperial"
    METRIC = "metric"


# Base Models
class APIStatus(BaseModel):
    """API response status information"""

    status_code: int = Field(description="Response status code (0 = SUCCESS)")
    status_message: str = Field(description="Status message description")


class Units(BaseModel):
    """Unit specifications for measurements"""

    units_temp: TemperatureUnit = Field(description="Temperature units")
    units_wind: WindUnit = Field(description="Wind speed units")
    units_pressure: PressureUnit = Field(description="Pressure units")
    units_precip: PrecipUnit = Field(description="Precipitation units")
    units_distance: DistanceUnit = Field(description="Distance units")
    units_direction: DirectionUnit | None = Field(None, description="Direction format")
    units_other: UnitSystem = Field(description="General unit system")


class Location(BaseModel):
    """Geographic location information"""

    latitude: float = Field(description="Latitude coordinate")
    longitude: float = Field(description="Longitude coordinate")
    timezone: str = Field(description="IANA timezone identifier", examples=["America/Los_Angeles"])
    timezone_offset_minutes: int = Field(
        description="UTC offset in minutes (negative for west of UTC)"
    )


# Device Models
class DeviceMeta(BaseModel):
    """Device-specific metadata"""

    agl: float = Field(description="Height above ground level in meters")
    environment: Environment = Field(description="Installation environment")
    name: str = Field(description="Device name/serial number")
    wifi_network_name: str | None = Field(None, description="Connected WiFi network name")


class DeviceSettings(BaseModel):
    """Device-specific configuration settings"""

    show_precip_final: bool | None = Field(
        None, description="Whether to show final precipitation values"
    )


class Device(BaseModel):
    """Weather station device information"""

    device_id: int = Field(description="Unique device identifier")
    device_type: DeviceType = Field(description="Type of device")
    serial_number: str | None = Field(None, description="Device serial number (None if inactive)")
    firmware_revision: str = Field(description="Current firmware version")
    hardware_revision: str = Field(description="Hardware revision number")
    device_meta: DeviceMeta = Field(description="Device-specific metadata")
    device_settings: DeviceSettings | None = Field(
        None, description="Device configuration settings"
    )


# Station Models
class StationMeta(BaseModel):
    """Station metadata"""

    elevation: float = Field(description="Station elevation in meters above sea level")
    share_with_wf: bool = Field(description="Whether data is shared with WeatherFlow")
    share_with_wu: bool = Field(description="Whether data is shared with Weather Underground")


class StationItem(BaseModel):
    """Station measurement item configuration"""

    item: str = Field(description="Type of measurement", examples=["air_temperature_humidity"])
    station_id: int = Field(description="Associated station ID")
    station_item_id: int = Field(description="Unique item identifier")
    location_id: int = Field(description="Location identifier")
    location_item_id: int = Field(description="Location-specific item identifier")
    device_id: int = Field(description="Device providing this measurement")
    sort: int | None = Field(None, description="Display sort order")


class StationCapability(BaseModel):
    """Station measurement capability"""

    capability: str = Field(description="Measurement capability type")
    device_id: int = Field(description="Device providing this capability")
    environment: Environment = Field(description="Operating environment")
    agl: float | None = Field(None, description="Height above ground level in meters")
    show_precip_final: bool | None = Field(None, description="Precipitation display setting")


class WeatherStation(BaseModel):
    """Complete weather station information"""

    station_id: int = Field(description="Unique identifier for the weather station")
    name: str = Field(description="Internal name of the weather station", examples=["Seattle"])
    public_name: str = Field(
        description="Public display name of the station", examples=["Fairview Ave E"]
    )
    latitude: float = Field(description="Latitude coordinate of the station")
    longitude: float = Field(description="Longitude coordinate of the station")
    timezone: str = Field(description="IANA timezone identifier", examples=["America/Los_Angeles"])
    timezone_offset_minutes: int = Field(
        description="UTC offset in minutes (negative for west of UTC)"
    )
    created_epoch: int = Field(description="Unix timestamp when the station was created")
    last_modified_epoch: int = Field(description="Unix timestamp of last station modification")
    is_local_mode: bool = Field(description="Whether the station is operating in local mode")
    station_meta: StationMeta = Field(description="Station metadata")
    devices: list[Device] = Field(description="Array of devices connected to the station")
    station_items: list[StationItem] = Field(
        description="Configuration of station measurement items"
    )
    capabilities: list[StationCapability] | None = Field(
        None, description="Station measurement capabilities"
    )


# Weather/Forecast Models
class DailyForecast(BaseModel):
    """Daily weather forecast"""

    air_temp_high: float = Field(description="High temperature")
    air_temp_low: float = Field(description="Low temperature")
    day_num: int = Field(ge=1, le=31, description="Day of month")
    day_start_local: int = Field(description="Unix timestamp for start of day in local time")
    month_num: int = Field(ge=1, le=12, description="Month number")
    icon: str = Field(description="Weather icon identifier", examples=["clear-day"])
    conditions: str = Field(description="Weather conditions description", examples=["Clear"])
    precip_probability: int = Field(
        ge=0, le=100, description="Precipitation probability percentage"
    )
    precip_type: str | None = Field(None, description="Type of precipitation", examples=["rain"])
    precip_icon: str | None = Field(None, description="Precipitation icon identifier")
    sunrise: int = Field(description="Unix timestamp for sunrise")
    sunset: int = Field(description="Unix timestamp for sunset")


class HourlyForecast(BaseModel):
    """Hourly weather forecast"""

    air_temperature: float = Field(description="Temperature")
    local_day: int = Field(description="Local day")
    local_hour: int = Field(ge=0, le=23, description="Local hour")
    time: int = Field(description="Unix timestamp")
    precip: float = Field(ge=0, description="Precipitation amount")
    precip_probability: int = Field(
        ge=0, le=100, description="Precipitation probability percentage"
    )
    precip_type: str | None = Field(None, description="Type of precipitation")
    relative_humidity: int = Field(ge=0, le=100, description="Relative humidity percentage")
    sea_level_pressure: float = Field(description="Atmospheric pressure")
    wind_avg: float = Field(ge=0, description="Average wind speed")
    wind_direction: float = Field(ge=0, le=360, description="Wind direction in degrees")
    wind_direction_cardinal: str = Field(description="Cardinal wind direction", examples=["NE"])
    wind_gust: float = Field(ge=0, description="Wind gust speed")
    conditions: str = Field(description="Weather conditions description")
    icon: str = Field(description="Weather icon identifier")
    feels_like: float = Field(description="Apparent temperature")
    uv: float = Field(ge=0, description="UV index")


class CurrentConditions(BaseModel):
    """Current weather conditions"""

    air_temperature: float = Field(description="Current temperature")
    conditions: str = Field(description="Current weather conditions")
    feels_like: float = Field(description="Apparent temperature")
    icon: str = Field(description="Current weather icon")
    relative_humidity: int = Field(ge=0, le=100, description="Current humidity percentage")
    sea_level_pressure: float = Field(description="Current pressure")
    wind_avg: float = Field(ge=0, description="Average wind speed")
    wind_gust: float = Field(ge=0, description="Wind gust speed")
    wind_direction: float = Field(ge=0, le=360, description="Wind direction in degrees")
    wind_direction_cardinal: str = Field(description="Cardinal wind direction")
    uv: int = Field(ge=0, description="Current UV index")
    time: int = Field(description="Unix timestamp of observation")
    # Additional measurements
    solar_radiation: float | None = Field(None, description="Solar radiation intensity")
    brightness: float | None = Field(None, description="Light intensity in lux")
    dew_point: float | None = Field(None, description="Dew point temperature")
    wet_bulb_temperature: float | None = Field(None, description="Wet bulb temperature")
    # Lightning data
    lightning_strike_last_epoch: int | None = Field(
        None, description="Unix timestamp of last lightning strike"
    )
    lightning_strike_last_distance: int | None = Field(
        None, description="Distance to last lightning strike"
    )
    lightning_strike_count: int | None = Field(None, description="Current lightning strike count")
    lightning_strike_count_last_1hr: int | None = Field(
        None, description="Lightning strikes in last hour"
    )
    lightning_strike_count_last_3hr: int | None = Field(
        None, description="Lightning strikes in last 3 hours"
    )
    # Precipitation accumulations
    precip_accum_last_1hr: float | None = Field(
        None, description="Precipitation accumulation in last hour"
    )
    precip_accum_local_day: float | None = Field(
        None, description="Precipitation accumulation for current local day"
    )
    precip_accum_local_yesterday: float | None = Field(
        None, description="Precipitation accumulation for yesterday"
    )


class Forecast(BaseModel):
    """Weather forecast data"""

    daily: list[DailyForecast] = Field(description="10-day daily forecast")
    hourly: list[HourlyForecast] = Field(description="Detailed hourly forecast")


# Observation Models
class WeatherObservation(BaseModel):
    """Detailed weather observation"""

    timestamp: int = Field(description="Unix timestamp of the observation")
    air_temperature: float = Field(description="Current air temperature")
    barometric_pressure: float = Field(description="Station barometric pressure")
    station_pressure: float = Field(description="Station-level atmospheric pressure")
    pressure_trend: PressureTrend = Field(description="Pressure trend")
    sea_level_pressure: float = Field(description="Sea level adjusted atmospheric pressure")
    relative_humidity: int = Field(ge=0, le=100, description="Relative humidity percentage")
    precip: float = Field(ge=0, description="Current precipitation rate")
    precip_accum_last_1hr: float = Field(
        ge=0, description="Precipitation accumulation in last hour"
    )
    precip_accum_local_day: float = Field(
        ge=0, description="Precipitation accumulation for current local day"
    )
    precip_accum_local_day_final: float = Field(
        ge=0, description="Final precipitation total for current day"
    )
    precip_accum_local_yesterday: float = Field(
        ge=0, description="Precipitation accumulation for yesterday"
    )
    precip_accum_local_yesterday_final: float = Field(
        ge=0, description="Final precipitation total for yesterday"
    )
    precip_analysis_type_yesterday: int = Field(
        description="Type of precipitation analysis for yesterday"
    )
    precip_minutes_local_day: int = Field(ge=0, description="Minutes of precipitation today")
    precip_minutes_local_yesterday: int = Field(
        ge=0, description="Minutes of precipitation yesterday"
    )
    precip_minutes_local_yesterday_final: int = Field(
        ge=0, description="Final minutes of precipitation yesterday"
    )
    wind_avg: float = Field(ge=0, description="Average wind speed")
    wind_direction: int = Field(ge=0, le=360, description="Wind direction in degrees")
    wind_gust: float = Field(ge=0, description="Wind gust speed")
    wind_lull: float = Field(ge=0, description="Wind lull (minimum wind speed)")
    solar_radiation: float = Field(ge=0, description="Solar radiation intensity")
    uv: float = Field(ge=0, description="UV index")
    brightness: float = Field(ge=0, description="Light intensity in lux")
    lightning_strike_last_epoch: int | None = Field(
        None, description="Unix timestamp of last lightning strike"
    )
    lightning_strike_last_distance: int | None = Field(
        None, description="Distance to last lightning strike"
    )
    lightning_strike_count: int = Field(ge=0, description="Current lightning strike count")
    lightning_strike_count_last_1hr: int = Field(ge=0, description="Lightning strikes in last hour")
    lightning_strike_count_last_3hr: int = Field(
        ge=0, description="Lightning strikes in last 3 hours"
    )
    feels_like: float = Field(description="Apparent temperature (heat index or wind chill)")
    heat_index: float = Field(description="Heat index temperature")
    wind_chill: float = Field(description="Wind chill temperature")
    dew_point: float = Field(description="Dew point temperature")
    wet_bulb_temperature: float = Field(description="Wet bulb temperature")
    wet_bulb_globe_temperature: float = Field(description="Wet bulb globe temperature")
    delta_t: float = Field(description="Delta T (difference between air temp and wet bulb temp)")
    air_density: float = Field(description="Air density")


# Main Response Models
class StationsResponse(BaseModel):
    """Response containing multiple weather stations"""

    stations: list[WeatherStation] = Field(description="Array of weather station objects")
    status: APIStatus = Field(description="API response status information")


class StationResponse(WeatherStation):
    """Response for a single weather station (inherits all WeatherStation fields)"""

    pass


class ForecastResponse(BaseModel):
    """Weather forecast response"""

    forecast: Forecast = Field(description="Weather forecast data")
    current_conditions: CurrentConditions = Field(description="Real-time weather observations")
    location_name: str = Field(
        description="Name of the weather station location", examples=["Seattle"]
    )
    latitude: float = Field(description="Latitude coordinate of the station")
    longitude: float = Field(description="Longitude coordinate of the station")
    timezone: str = Field(description="IANA timezone identifier", examples=["America/Los_Angeles"])
    timezone_offset_minutes: int = Field(description="UTC offset in minutes")
    units: Units = Field(description="Unit specifications for all measurements")


class ObservationResponse(BaseModel):
    """Weather observation response"""

    outdoor_keys: list[str] = Field(description="List of available outdoor measurement field names")
    obs: list[WeatherObservation] = Field(description="Array of observation records")
    station_id: int = Field(description="Unique identifier for the weather station")
    station_name: str = Field(description="Name of the weather station", examples=["Seattle"])
    public_name: str = Field(
        description="Public display name of the station", examples=["Lake Union"]
    )
    latitude: float = Field(description="Latitude coordinate of the station")
    longitude: float = Field(description="Longitude coordinate of the station")
    elevation: float = Field(description="Elevation of the station in meters")
    is_public: bool = Field(description="Whether the station data is publicly accessible")
    timezone: str = Field(description="IANA timezone identifier", examples=["America/Los_Angeles"])
    station_units: Units = Field(description="Unit specifications for all measurements")
    status: APIStatus = Field(description="API response status information")
