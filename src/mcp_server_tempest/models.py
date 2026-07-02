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
    status_message: str


class Units(BaseModel):
    """Unit specifications for measurements"""

    units_temp: TemperatureUnit
    units_wind: WindUnit
    units_pressure: PressureUnit
    units_precip: PrecipUnit
    units_distance: DistanceUnit
    units_direction: DirectionUnit | None = None
    units_other: UnitSystem


class Location(BaseModel):
    """Geographic location information"""

    latitude: float
    longitude: float
    timezone: str = Field(description="IANA timezone identifier", examples=["America/Los_Angeles"])
    timezone_offset_minutes: int = Field(
        description="UTC offset in minutes (negative for west of UTC)"
    )


# Device Models
class DeviceMeta(BaseModel):
    """Device-specific metadata"""

    agl: float = Field(description="Height above ground level in meters")
    environment: Environment
    name: str = Field(description="Device name/serial number")
    wifi_network_name: str | None = None


class DeviceSettings(BaseModel):
    """Device-specific configuration settings"""

    show_precip_final: bool | None = None


class Device(BaseModel):
    """Weather station device information"""

    device_id: int
    device_type: DeviceType
    serial_number: str | None = Field(None, description="Device serial number (None if inactive)")
    firmware_revision: str
    hardware_revision: str
    device_meta: DeviceMeta
    device_settings: DeviceSettings | None = None


# Station Models
class StationMeta(BaseModel):
    """Station metadata"""

    elevation: float = Field(description="Station elevation in meters above sea level")
    share_with_wf: bool = Field(description="Whether data is shared with WeatherFlow")
    share_with_wu: bool = Field(description="Whether data is shared with Weather Underground")


class StationItem(BaseModel):
    """Station measurement item configuration"""

    item: str = Field(examples=["air_temperature_humidity"])
    station_id: int
    station_item_id: int
    location_id: int
    location_item_id: int
    device_id: int
    sort: int | None = None


class StationCapability(BaseModel):
    """Station measurement capability"""

    capability: str
    device_id: int
    environment: Environment
    agl: float | None = Field(None, description="Height above ground level in meters")
    show_precip_final: bool | None = None


class WeatherStation(BaseModel):
    """Complete weather station information"""

    station_id: int
    name: str = Field(description="Internal name of the weather station", examples=["Seattle"])
    public_name: str = Field(
        description="Public display name of the station", examples=["Fairview Ave E"]
    )
    latitude: float
    longitude: float
    timezone: str = Field(description="IANA timezone identifier", examples=["America/Los_Angeles"])
    timezone_offset_minutes: int = Field(
        description="UTC offset in minutes (negative for west of UTC)"
    )
    created_epoch: int = Field(description="Unix timestamp when the station was created")
    last_modified_epoch: int = Field(description="Unix timestamp of last station modification")
    is_local_mode: bool
    station_meta: StationMeta
    devices: list[Device]
    station_items: list[StationItem]
    capabilities: list[StationCapability] | None = None


# Weather/Forecast Models
class DailyForecast(BaseModel):
    """Daily weather forecast"""

    air_temp_high: float
    air_temp_low: float
    day_num: int = Field(ge=1, le=31)
    day_start_local: int = Field(description="Unix timestamp for start of day in local time")
    month_num: int = Field(ge=1, le=12)
    icon: str = Field(examples=["clear-day"])
    conditions: str = Field(examples=["Clear"])
    precip_probability: int = Field(ge=0, le=100)
    precip_type: str | None = Field(None, examples=["rain"])
    precip_icon: str | None = None
    sunrise: int = Field(description="Unix timestamp for sunrise")
    sunset: int = Field(description="Unix timestamp for sunset")


class HourlyForecast(BaseModel):
    """Hourly weather forecast"""

    air_temperature: float
    local_day: int
    local_hour: int = Field(ge=0, le=23)
    time: int = Field(description="Unix timestamp")
    precip: float = Field(ge=0, description="Precipitation amount")
    precip_probability: int = Field(ge=0, le=100)
    precip_type: str | None = None
    relative_humidity: int = Field(ge=0, le=100)
    sea_level_pressure: float
    wind_avg: float = Field(ge=0)
    wind_direction: float = Field(ge=0, le=360, description="Wind direction in degrees")
    wind_direction_cardinal: str = Field(examples=["NE"])
    wind_gust: float = Field(ge=0)
    conditions: str
    icon: str
    feels_like: float = Field(description="Apparent temperature")
    uv: float = Field(ge=0)


class CurrentConditions(BaseModel):
    """Current weather conditions"""

    air_temperature: float
    conditions: str
    feels_like: float = Field(description="Apparent temperature")
    icon: str
    relative_humidity: int = Field(ge=0, le=100)
    sea_level_pressure: float
    wind_avg: float = Field(ge=0)
    wind_gust: float = Field(ge=0)
    wind_direction: float = Field(ge=0, le=360, description="Wind direction in degrees")
    wind_direction_cardinal: str
    uv: int = Field(ge=0)
    time: int = Field(description="Unix timestamp of observation")
    # Additional measurements
    solar_radiation: float | None = None
    brightness: float | None = Field(None, description="Light intensity in lux")
    dew_point: float | None = None
    wet_bulb_temperature: float | None = None
    # Lightning data
    lightning_strike_last_epoch: int | None = Field(
        None, description="Unix timestamp of last lightning strike"
    )
    lightning_strike_last_distance: int | None = None
    lightning_strike_count: int | None = None
    lightning_strike_count_last_1hr: int | None = None
    lightning_strike_count_last_3hr: int | None = None
    # Precipitation accumulations
    precip_accum_last_1hr: float | None = None
    precip_accum_local_day: float | None = None
    precip_accum_local_yesterday: float | None = None


class Forecast(BaseModel):
    """Weather forecast data"""

    daily: list[DailyForecast]
    hourly: list[HourlyForecast]


# Observation Models
class WeatherObservation(BaseModel):
    """Detailed weather observation"""

    timestamp: int = Field(description="Unix timestamp of the observation")
    air_temperature: float
    barometric_pressure: float
    station_pressure: float = Field(description="Station-level atmospheric pressure")
    pressure_trend: PressureTrend
    sea_level_pressure: float = Field(description="Sea level adjusted atmospheric pressure")
    relative_humidity: int = Field(ge=0, le=100)
    precip: float = Field(ge=0, description="Current precipitation rate")
    precip_accum_last_1hr: float = Field(ge=0)
    precip_accum_local_day: float = Field(ge=0)
    precip_accum_local_day_final: float = Field(
        ge=0, description="Final precipitation total for current day"
    )
    precip_accum_local_yesterday: float = Field(ge=0)
    precip_accum_local_yesterday_final: float = Field(
        ge=0, description="Final precipitation total for yesterday"
    )
    precip_analysis_type_yesterday: int
    precip_minutes_local_day: int = Field(ge=0)
    precip_minutes_local_yesterday: int = Field(ge=0)
    precip_minutes_local_yesterday_final: int = Field(
        ge=0, description="Final minutes of precipitation yesterday"
    )
    wind_avg: float = Field(ge=0)
    wind_direction: int = Field(ge=0, le=360, description="Wind direction in degrees")
    wind_gust: float = Field(ge=0)
    wind_lull: float = Field(ge=0, description="Wind lull (minimum wind speed)")
    solar_radiation: float = Field(ge=0)
    uv: float = Field(ge=0)
    brightness: float = Field(ge=0, description="Light intensity in lux")
    lightning_strike_last_epoch: int | None = Field(
        None, description="Unix timestamp of last lightning strike"
    )
    lightning_strike_last_distance: int | None = None
    lightning_strike_count: int = Field(ge=0)
    lightning_strike_count_last_1hr: int = Field(ge=0)
    lightning_strike_count_last_3hr: int = Field(ge=0)
    feels_like: float = Field(description="Apparent temperature (heat index or wind chill)")
    heat_index: float
    wind_chill: float
    dew_point: float
    wet_bulb_temperature: float
    wet_bulb_globe_temperature: float
    delta_t: float = Field(description="Delta T (difference between air temp and wet bulb temp)")
    air_density: float


# Main Response Models
class StationsResponse(BaseModel):
    """Response containing multiple weather stations"""

    stations: list[WeatherStation]
    status: APIStatus


class StationResponse(WeatherStation):
    """Response for a single weather station (inherits all WeatherStation fields)"""

    pass


class ForecastResponse(BaseModel):
    """Weather forecast response"""

    forecast: Forecast
    current_conditions: CurrentConditions
    location_name: str = Field(examples=["Seattle"])
    latitude: float
    longitude: float
    timezone: str = Field(description="IANA timezone identifier", examples=["America/Los_Angeles"])
    timezone_offset_minutes: int = Field(description="UTC offset in minutes")
    units: Units
    # Truncation transparency. Populated by the get_forecast tool, not the
    # upstream API; defaults keep `ForecastResponse(**raw_upstream)` working.
    truncated: bool = Field(
        default=False,
        description=(
            "True iff fewer entries were returned than the agent EXPLICITLY "
            "requested (returned_hours < requested_hours or returned_days < "
            "requested_days). A plain call that omits hours/days is never "
            "truncated. The only cause is an upstream shortfall: explicit "
            "hours/days are honored as given in both summary and detailed "
            "modes, so no server-side cap can clip them."
        ),
    )
    requested_hours: int | None = Field(
        default=None,
        description="hours value the agent explicitly requested; omitted when not provided.",
    )
    requested_days: int | None = Field(
        default=None,
        description="days value the agent explicitly requested; omitted when not provided.",
    )
    returned_hours: int | None = Field(
        default=None, description="Number of hourly entries actually returned."
    )
    returned_days: int | None = Field(
        default=None, description="Number of daily entries actually returned."
    )
    truncation_hint: str | None = Field(
        default=None,
        description=(
            "Factual note, present only when truncated=true; states how many "
            "entries upstream supplied versus the explicit request. Not a "
            "repair — the missing entries do not exist upstream."
        ),
    )


class ObservationResponse(BaseModel):
    """Weather observation response"""

    outdoor_keys: list[str] = Field(description="List of available outdoor measurement field names")
    obs: list[WeatherObservation]
    station_id: int
    station_name: str = Field(examples=["Seattle"])
    public_name: str = Field(
        description="Public display name of the station", examples=["Lake Union"]
    )
    latitude: float
    longitude: float
    elevation: float = Field(description="Elevation of the station in meters")
    is_public: bool
    timezone: str = Field(description="IANA timezone identifier", examples=["America/Los_Angeles"])
    station_units: Units
    status: APIStatus
