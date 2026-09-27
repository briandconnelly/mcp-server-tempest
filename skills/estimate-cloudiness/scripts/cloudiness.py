#!/usr/bin/env python3
"""Estimate sky condition from a Tempest station's solar radiation reading.

Compares observed solar radiation to modeled clear-sky irradiance for the
station's location at the observation time, and reports a clearness index
(observed / expected) with a sky-condition category.

Solar position: NOAA solar calculator algorithm (validated to within 0.01
degrees of pvlib's SPA implementation). Clear-sky GHI: Haurwitz (1945)
model as formulated in Reno et al. (2012), the same form pvlib implements,
with an approximate station-pressure scaling of the extinction term.

Stdlib only; no third-party dependencies.

Usage:
  cloudiness.py --lat 47.641 --lon -122.330 --timestamp 1783040789 \
      --solar-radiation 178 [--pressure 1014.9]

Output: a single JSON object on stdout. Key fields:
  status    "ok" | "night" | "sun_too_low"
  category  sky-condition band (only when status is "ok")
  clearness_index  observed / expected clear-sky ratio
  notes     caveats that apply to this specific reading
"""

import argparse
import json
import math
import sys
from datetime import datetime, timezone

# Below this apparent solar elevation (degrees) the clearness index is
# meaningless: expected irradiance is tiny and horizon obstructions dominate.
MIN_USABLE_ELEVATION = 5.0
# Between MIN_USABLE_ELEVATION and this, report with low confidence.
LOW_CONFIDENCE_ELEVATION = 15.0
# Above this clearness index the reading is outside the plausible sustained
# range; brief extreme cloud-edge enhancement spikes or a sensor/data problem
# (fault, reflection, wrong timestamp/location) are the likely causes.
IMPLAUSIBLE_CI = 1.6

CATEGORY_BANDS = [
    # (minimum clearness index, category, description)
    (
        1.15,
        "sun_and_broken_clouds",
        "Sun unobstructed with bright broken clouds nearby (cloud-edge "
        "enhancement) -- partly cloudy sky",
    ),
    (0.80, "clear", "Clear or nearly clear -- sun unobstructed, at most thin haze"),
    (
        0.45,
        "thin_or_partial",
        "Thin high clouds or haze, or sun partially obscured -- anywhere from "
        "hazy sun to bright overcast; could be one moment of a partly cloudy "
        "sky",
    ),
    (0.15, "cloudy", "Sun obscured -- mostly cloudy to overcast"),
    (0.0, "thick_overcast", "Thick overcast, heavy rain, or fog"),
]


def solar_position(lat: float, lon: float, dt: datetime) -> dict:
    """Compute solar elevation and azimuth using the NOAA algorithm.

    Args:
        lat: Latitude in degrees (north positive).
        lon: Longitude in degrees (east positive).
        dt: Timezone-aware datetime in UTC.

    Returns:
        Dict with 'elevation' (geometric), 'apparent_elevation'
        (refraction-corrected), and 'azimuth' in degrees.
    """
    hour_utc = dt.hour + dt.minute / 60 + dt.second / 3600

    # Julian date (valid for Gregorian-calendar CE dates)
    jd = (
        367 * dt.year
        - int(7 * (dt.year + int((dt.month + 9) / 12)) / 4)
        + int(275 * dt.month / 9)
        + dt.day
        + 1721013.5
        + hour_utc / 24
    )
    jc = (jd - 2451545.0) / 36525.0  # Julian century

    geom_mean_long = (280.46646 + jc * (36000.76983 + 0.0003032 * jc)) % 360
    geom_mean_anom = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    ecc = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)

    sun_eq_ctr = (
        math.sin(math.radians(geom_mean_anom)) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
        + math.sin(math.radians(2 * geom_mean_anom)) * (0.019993 - 0.000101 * jc)
        + math.sin(math.radians(3 * geom_mean_anom)) * 0.000289
    )
    sun_true_long = geom_mean_long + sun_eq_ctr
    sun_app_long = (
        sun_true_long - 0.00569 - 0.00478 * math.sin(math.radians(125.04 - 1934.136 * jc))
    )

    mean_obliq = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60
    obliq_corr = mean_obliq + 0.00256 * math.cos(math.radians(125.04 - 1934.136 * jc))

    decl = math.degrees(
        math.asin(math.sin(math.radians(obliq_corr)) * math.sin(math.radians(sun_app_long)))
    )

    # Equation of time (minutes)
    var_y = math.tan(math.radians(obliq_corr / 2)) ** 2
    eq_time = 4 * math.degrees(
        var_y * math.sin(2 * math.radians(geom_mean_long))
        - 2 * ecc * math.sin(math.radians(geom_mean_anom))
        + 4
        * ecc
        * var_y
        * math.sin(math.radians(geom_mean_anom))
        * math.cos(2 * math.radians(geom_mean_long))
        - 0.5 * var_y**2 * math.sin(4 * math.radians(geom_mean_long))
        - 1.25 * ecc**2 * math.sin(2 * math.radians(geom_mean_anom))
    )

    time_offset = eq_time + 4 * lon  # minutes
    true_solar_time = (hour_utc * 60 + time_offset) % 1440
    hour_angle = true_solar_time / 4 - 180

    lat_r = math.radians(lat)
    decl_r = math.radians(decl)
    cos_zenith = math.sin(lat_r) * math.sin(decl_r) + math.cos(lat_r) * math.cos(decl_r) * math.cos(
        math.radians(hour_angle)
    )
    cos_zenith = max(-1, min(1, cos_zenith))
    zenith = math.degrees(math.acos(cos_zenith))
    elevation = 90 - zenith

    # Atmospheric refraction correction (NOAA / Meeus approximation)
    if elevation > 85:
        refraction = 0.0
    elif elevation > 5:
        refraction = (
            58.1 / math.tan(math.radians(elevation))
            - 0.07 / math.tan(math.radians(elevation)) ** 3
            + 0.000086 / math.tan(math.radians(elevation)) ** 5
        ) / 3600
    elif elevation > -0.575:
        refraction = (
            1735
            + elevation * (-518.2 + elevation * (103.4 + elevation * (-12.79 + elevation * 0.711)))
        ) / 3600
    else:
        refraction = -20.774 / (3600 * math.tan(math.radians(elevation)))

    apparent_elevation = elevation + refraction

    sin_zenith = math.sin(math.radians(zenith))
    if sin_zenith == 0:
        azimuth = 0.0
    else:
        cos_az = (math.sin(lat_r) * cos_zenith - math.sin(decl_r)) / (math.cos(lat_r) * sin_zenith)
        cos_az = max(-1, min(1, cos_az))
        if hour_angle > 0:
            azimuth = (math.degrees(math.acos(cos_az)) + 180) % 360
        else:
            azimuth = (540 - math.degrees(math.acos(cos_az))) % 360

    return {
        "elevation": elevation,
        "apparent_elevation": apparent_elevation,
        "azimuth": azimuth,
    }


def clear_sky_ghi(apparent_elevation: float, pressure_mbar: float = 1013.25) -> float:
    """Clear-sky GHI in W/m² via Haurwitz (Reno et al. 2012 formulation).

    The extinction term is scaled by station pressure relative to standard
    sea-level pressure, so high-altitude stations (thinner atmosphere) get a
    slightly higher expected value. The scaling is approximate (Haurwitz's
    coefficient is an empirical whole-atmosphere fit, not pure Rayleigh
    extinction) and is clamped to a physically sensible range.

    Args:
        apparent_elevation: Refraction-corrected solar elevation in degrees.
        pressure_mbar: Station-level (not sea-level) pressure in mbar/hPa.

    Returns:
        Estimated clear-sky GHI in W/m²; 0.0 when the sun is at or below
        the horizon.
    """
    if apparent_elevation <= 0:
        return 0.0
    cos_z = math.cos(math.radians(90 - apparent_elevation))
    pressure_ratio = max(0.6, min(1.05, pressure_mbar / 1013.25))
    return 1098 * cos_z * math.exp(-0.059 * pressure_ratio / cos_z)


def estimate(
    lat: float,
    lon: float,
    timestamp: int,
    solar_radiation: float,
    pressure_mbar: float = 1013.25,
) -> dict:
    """Estimate sky condition from one observation. Returns a JSON-safe dict."""
    dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    sun = solar_position(lat, lon, dt_utc)
    el = sun["apparent_elevation"]

    result = {
        "time_utc": dt_utc.isoformat(),
        "solar_elevation_deg": round(el, 1),
        "solar_azimuth_deg": round(sun["azimuth"], 1),
        "observed_wm2": solar_radiation,
        "expected_clear_sky_wm2": None,
        "clearness_index": None,
        "status": "ok",
        "category": None,
        "description": None,
        "confidence": None,
        "notes": [],
    }

    if el <= 0:
        result["status"] = "night"
        result["notes"].append(
            "Sun is below the horizon at the observation time; cloudiness "
            "cannot be measured from solar radiation."
        )
        return result

    if el < MIN_USABLE_ELEVATION:
        result["status"] = "sun_too_low"
        result["notes"].append(
            f"Sun is only {el:.1f} degrees above the horizon; expected "
            "irradiance is too small and horizon obstructions too likely "
            "for a meaningful clearness index."
        )
        return result

    expected = clear_sky_ghi(el, pressure_mbar)
    ci = solar_radiation / expected
    result["expected_clear_sky_wm2"] = round(expected, 1)
    result["clearness_index"] = round(ci, 3)

    if ci > IMPLAUSIBLE_CI:
        result["status"] = "ok"
        result["category"] = "implausible"
        result["description"] = (
            "Observed radiation far exceeds the expected clear-sky value -- "
            "either a brief extreme cloud-edge enhancement spike or a "
            "sensor/data problem (fault, reflection, wrong "
            "timestamp/location); re-check in a few minutes."
        )
        result["confidence"] = "none"
        return result

    for threshold, category, description in CATEGORY_BANDS:
        if ci >= threshold:
            result["category"] = category
            result["description"] = description
            break

    if el < LOW_CONFIDENCE_ELEVATION:
        result["confidence"] = "low"
        result["notes"].append(
            "Low sun angle: the clear-sky model and the sensor's cosine "
            "response are least accurate near the horizon, and shading by "
            "trees or buildings can mimic cloud."
        )
    else:
        result["confidence"] = "high"

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Estimate sky condition from Tempest solar radiation."
    )
    parser.add_argument(
        "--lat",
        type=float,
        required=True,
        help="Station latitude in degrees (north positive)",
    )
    parser.add_argument(
        "--lon",
        type=float,
        required=True,
        help="Station longitude in degrees (east positive)",
    )
    parser.add_argument(
        "--timestamp",
        type=int,
        required=True,
        help="Observation Unix epoch timestamp (UTC seconds)",
    )
    parser.add_argument(
        "--solar-radiation",
        type=float,
        required=True,
        help="Observed solar radiation in W/m²",
    )
    parser.add_argument(
        "--pressure",
        type=float,
        default=1013.25,
        help="Station-level pressure in mbar/hPa "
        "(station_pressure or barometric_pressure; "
        "default: 1013.25)",
    )
    args = parser.parse_args()

    for name, value in (
        ("--lat", args.lat),
        ("--lon", args.lon),
        ("--solar-radiation", args.solar_radiation),
        ("--pressure", args.pressure),
    ):
        if not math.isfinite(value):
            parser.error(f"{name} must be a finite number")
    if args.solar_radiation < 0:
        parser.error("--solar-radiation must be non-negative")
    if args.pressure <= 0:
        parser.error("--pressure must be positive")
    if not -90 <= args.lat <= 90:
        parser.error("--lat must be between -90 and 90")
    if not -180 <= args.lon <= 180:
        parser.error("--lon must be between -180 and 180")

    result = estimate(args.lat, args.lon, args.timestamp, args.solar_radiation, args.pressure)
    json.dump(result, sys.stdout, indent=2, allow_nan=False)
    print()


if __name__ == "__main__":
    main()
