"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from mcp_server_tempest.models import (
    APIStatus,
    CurrentConditions,
    DailyForecast,
    Device,
    DeviceType,
    Environment,
    Forecast,
    ForecastResponse,
    HourlyForecast,
    Location,
    ObservationResponse,
    PressureTrend,
    StationsResponse,
    Units,
    WeatherObservation,
    WeatherStation,
)


def _make_units(**overrides):
    defaults = {
        "units_temp": "f",
        "units_wind": "mph",
        "units_pressure": "inhg",
        "units_precip": "in",
        "units_distance": "mi",
        "units_other": "imperial",
    }
    return Units(**(defaults | overrides))


def _make_device(**overrides):
    defaults = {
        "device_id": 1,
        "device_type": "ST",
        "serial_number": "ST-00001234",
        "firmware_revision": "1.0",
        "hardware_revision": "1",
        "device_meta": {
            "agl": 2.0,
            "environment": "outdoor",
            "name": "Tempest",
        },
    }
    return Device(**(defaults | overrides))


def _make_station(**overrides):
    defaults = {
        "station_id": 12345,
        "name": "Home",
        "public_name": "My Station",
        "latitude": 47.6,
        "longitude": -122.3,
        "timezone": "America/Los_Angeles",
        "timezone_offset_minutes": -420,
        "created_epoch": 1700000000,
        "last_modified_epoch": 1700000000,
        "is_local_mode": False,
        "station_meta": {"elevation": 50.0, "share_with_wf": True, "share_with_wu": False},
        "devices": [_make_device().model_dump()],
        "station_items": [],
    }
    return WeatherStation(**(defaults | overrides))


class TestEnums:
    def test_device_type_values(self):
        assert DeviceType.TEMPEST.value == "ST"
        assert DeviceType.HUB.value == "HB"

    def test_environment_values(self):
        assert Environment.INDOOR.value == "indoor"
        assert Environment.OUTDOOR.value == "outdoor"

    def test_pressure_trend_values(self):
        assert PressureTrend.STEADY.value == "steady"
        assert PressureTrend.RISING.value == "rising"
        assert PressureTrend.FALLING.value == "falling"


class TestAPIStatus:
    def test_valid(self):
        status = APIStatus(status_code=0, status_message="SUCCESS")
        assert status.status_code == 0
        assert status.status_message == "SUCCESS"


class TestUnits:
    def test_valid(self):
        units = _make_units()
        assert units.units_temp.value == "f"
        assert units.units_other.value == "imperial"

    def test_optional_direction(self):
        units = _make_units(units_direction="cardinal")
        assert units.units_direction.value == "cardinal"

        units = _make_units()
        assert units.units_direction is None


class TestLocation:
    def test_valid(self):
        loc = Location(
            latitude=47.6,
            longitude=-122.3,
            timezone="America/Los_Angeles",
            timezone_offset_minutes=-420,
        )
        assert loc.latitude == 47.6


class TestDevice:
    def test_valid(self):
        device = _make_device()
        assert device.device_type == DeviceType.TEMPEST
        assert device.device_meta.environment == Environment.OUTDOOR

    def test_optional_serial_number(self):
        device = _make_device(serial_number=None)
        assert device.serial_number is None


class TestWeatherStation:
    def test_valid(self):
        station = _make_station()
        assert station.station_id == 12345
        assert len(station.devices) == 1
        assert station.devices[0].device_type == DeviceType.TEMPEST


class TestStationsResponse:
    def test_valid(self):
        resp = StationsResponse(
            stations=[_make_station().model_dump()],
            status={"status_code": 0, "status_message": "SUCCESS"},
        )
        assert len(resp.stations) == 1
        assert resp.status.status_code == 0


class TestDailyForecast:
    def test_valid(self):
        fc = DailyForecast(
            air_temp_high=75.0,
            air_temp_low=55.0,
            day_num=15,
            day_start_local=1700000000,
            month_num=3,
            icon="clear-day",
            conditions="Clear",
            precip_probability=10,
            sunrise=1700000000,
            sunset=1700040000,
        )
        assert fc.air_temp_high == 75.0

    def test_precip_probability_bounds(self):
        with pytest.raises(ValidationError):
            DailyForecast(
                air_temp_high=75.0,
                air_temp_low=55.0,
                day_num=15,
                day_start_local=1700000000,
                month_num=3,
                icon="clear-day",
                conditions="Clear",
                precip_probability=150,
                sunrise=1700000000,
                sunset=1700040000,
            )


class TestHourlyForecast:
    def test_valid(self):
        hf = HourlyForecast(
            air_temperature=68.0,
            local_day=15,
            local_hour=14,
            time=1700000000,
            precip=0.0,
            precip_probability=5,
            relative_humidity=45,
            sea_level_pressure=30.1,
            wind_avg=5.0,
            wind_direction=180.0,
            wind_direction_cardinal="S",
            wind_gust=8.0,
            conditions="Clear",
            icon="clear-day",
            feels_like=68.0,
            uv=3.0,
        )
        assert hf.local_hour == 14


class TestCurrentConditions:
    def test_valid(self):
        cc = CurrentConditions(
            air_temperature=72.0,
            conditions="Partly Cloudy",
            feels_like=72.0,
            icon="partly-cloudy-day",
            relative_humidity=50,
            sea_level_pressure=30.1,
            wind_avg=5.0,
            wind_gust=10.0,
            wind_direction=270.0,
            wind_direction_cardinal="W",
            uv=4,
            time=1700000000,
        )
        assert cc.air_temperature == 72.0


class TestWeatherObservation:
    def _make_observation(self, **overrides):
        defaults = {
            "timestamp": 1700000000,
            "air_temperature": 72.0,
            "barometric_pressure": 30.1,
            "station_pressure": 29.9,
            "pressure_trend": "steady",
            "sea_level_pressure": 30.1,
            "relative_humidity": 50,
            "precip": 0.0,
            "precip_accum_last_1hr": 0.0,
            "precip_accum_local_day": 0.0,
            "precip_accum_local_day_final": 0.0,
            "precip_accum_local_yesterday": 0.0,
            "precip_accum_local_yesterday_final": 0.0,
            "precip_analysis_type_yesterday": 0,
            "precip_minutes_local_day": 0,
            "precip_minutes_local_yesterday": 0,
            "precip_minutes_local_yesterday_final": 0,
            "wind_avg": 5.0,
            "wind_direction": 180,
            "wind_gust": 10.0,
            "wind_lull": 2.0,
            "solar_radiation": 500.0,
            "uv": 3.0,
            "brightness": 50000.0,
            "lightning_strike_count": 0,
            "lightning_strike_count_last_1hr": 0,
            "lightning_strike_count_last_3hr": 0,
            "feels_like": 72.0,
            "heat_index": 72.0,
            "wind_chill": 72.0,
            "dew_point": 55.0,
            "wet_bulb_temperature": 60.0,
            "wet_bulb_globe_temperature": 65.0,
            "delta_t": 12.0,
            "air_density": 1.2,
        }
        return WeatherObservation(**(defaults | overrides))

    def test_valid(self):
        obs = self._make_observation()
        assert obs.pressure_trend == PressureTrend.STEADY

    def test_humidity_bounds(self):
        with pytest.raises(ValidationError):
            self._make_observation(relative_humidity=150)


class TestForecastResponse:
    def test_valid(self):
        resp = ForecastResponse(
            forecast={
                "daily": [],
                "hourly": [],
            },
            current_conditions={
                "air_temperature": 72.0,
                "conditions": "Clear",
                "feels_like": 72.0,
                "icon": "clear-day",
                "relative_humidity": 50,
                "sea_level_pressure": 30.1,
                "wind_avg": 5.0,
                "wind_gust": 10.0,
                "wind_direction": 180.0,
                "wind_direction_cardinal": "S",
                "uv": 3,
                "time": 1700000000,
            },
            location_name="Seattle",
            latitude=47.6,
            longitude=-122.3,
            timezone="America/Los_Angeles",
            timezone_offset_minutes=-420,
            units=_make_units().model_dump(),
        )
        assert resp.location_name == "Seattle"
        assert isinstance(resp.forecast, Forecast)


class TestObservationResponse:
    def test_valid(self):
        resp = ObservationResponse(
            outdoor_keys=["air_temperature"],
            obs=[],
            station_id=12345,
            station_name="Home",
            public_name="My Station",
            latitude=47.6,
            longitude=-122.3,
            elevation=50.0,
            is_public=True,
            timezone="America/Los_Angeles",
            station_units=_make_units().model_dump(),
            status={"status_code": 0, "status_message": "SUCCESS"},
        )
        assert resp.station_id == 12345
