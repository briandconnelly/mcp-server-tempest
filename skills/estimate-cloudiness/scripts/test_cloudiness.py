"""Regression tests for cloudiness.py.

Stdlib-only; run with:  python3 -m unittest test_cloudiness -v
"""

import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cloudiness import (  # noqa: E402
    CATEGORY_BANDS,
    IMPLAUSIBLE_CI,
    clear_sky_ghi,
    estimate,
    solar_position,
)

SCRIPT = Path(__file__).parent / "cloudiness.py"

# Seattle station, 2026-07-03T01:06:29Z: apparent solar elevation 27.9 deg,
# expected clear-sky GHI ~452.6 W/m² (verified against pvlib).
LAT, LON = 47.64132, -122.3299
TS_DAY = 1783040789
TS_NIGHT = 1783080000  # elevation ~ -3 deg
TS_LOW_SUN = 1783082000  # elevation ~ 1.8 deg


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


class TestSolarPosition(unittest.TestCase):
    def test_matches_reference_at_known_time(self):
        from datetime import datetime, timezone

        sun = solar_position(LAT, LON, datetime.fromtimestamp(TS_DAY, tz=timezone.utc))
        # Reference values from pvlib SPA for this time/place.
        self.assertAlmostEqual(sun["apparent_elevation"], 27.9, delta=0.1)
        self.assertAlmostEqual(sun["azimuth"], 274.3, delta=0.1)


class TestClearSkyGhi(unittest.TestCase):
    def test_zero_at_and_below_horizon(self):
        self.assertEqual(clear_sky_ghi(0.0), 0.0)
        self.assertEqual(clear_sky_ghi(-5.0), 0.0)

    def test_monotonic_in_elevation(self):
        values = [clear_sky_ghi(el) for el in range(5, 91, 5)]
        self.assertEqual(values, sorted(values))

    def test_lower_pressure_raises_expected(self):
        self.assertGreater(clear_sky_ghi(45, 850), clear_sky_ghi(45, 1013.25))

    def test_pressure_ratio_clamped(self):
        # Absurd pressures must not produce absurd GHI.
        self.assertEqual(clear_sky_ghi(45, 1), clear_sky_ghi(45, 0.6 * 1013.25))
        self.assertEqual(clear_sky_ghi(45, 5000), clear_sky_ghi(45, 1.05 * 1013.25))


class TestStatuses(unittest.TestCase):
    def test_night(self):
        r = estimate(LAT, LON, TS_NIGHT, 0)
        self.assertEqual(r["status"], "night")
        self.assertIsNone(r["category"])
        self.assertIsNone(r["clearness_index"])

    def test_sun_too_low_reports_no_index(self):
        # Regression: the pre-review script reported ci=4.78 "clear" here.
        r = estimate(LAT, LON, TS_LOW_SUN, 25)
        self.assertEqual(r["status"], "sun_too_low")
        self.assertIsNone(r["category"])
        self.assertIsNone(r["clearness_index"])


class TestCategoryBands(unittest.TestCase):
    def ci_for(self, ci: float) -> dict:
        expected = clear_sky_ghi(27.9, 1013.25)
        return estimate(LAT, LON, TS_DAY, ci * expected)

    def test_exact_boundaries_take_upper_band(self):
        for threshold, category, _ in CATEGORY_BANDS:
            if threshold == 0.0:
                continue
            self.assertEqual(self.ci_for(threshold)["category"], category)

    def test_band_interiors(self):
        for ci, category in [
            (0.05, "thick_overcast"),
            (0.3, "cloudy"),
            (0.6, "thin_or_partial"),
            (0.95, "clear"),
            (1.3, "sun_and_broken_clouds"),
        ]:
            self.assertEqual(self.ci_for(ci)["category"], category)

    def test_extreme_enhancement_is_anomalous_not_fault(self):
        r = self.ci_for(IMPLAUSIBLE_CI + 0.5)
        self.assertEqual(r["category"], "implausible")
        self.assertEqual(r["confidence"], "none")
        # Softened wording: must mention enhancement, not just assert a fault.
        self.assertIn("enhancement", r["description"])

    def test_low_sun_gives_low_confidence(self):
        r = estimate(LAT, LON, TS_LOW_SUN + 3000, 60)  # elevation ~ 8.9 deg
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["confidence"], "low")


class TestCli(unittest.TestCase):
    def test_valid_json_output(self):
        p = run_cli(
            "--lat",
            str(LAT),
            "--lon",
            str(LON),
            "--timestamp",
            str(TS_DAY),
            "--solar-radiation",
            "178",
            "--pressure",
            "1014.9",
        )
        self.assertEqual(p.returncode, 0)
        r = json.loads(p.stdout)  # strict: would fail on NaN/Infinity
        self.assertEqual(r["category"], "cloudy")
        self.assertTrue(math.isfinite(r["clearness_index"]))

    def test_rejects_non_finite_inputs(self):
        base = ["--lat", str(LAT), "--lon", str(LON), "--timestamp", str(TS_DAY)]
        for bad in (
            base + ["--solar-radiation", "nan"],
            base + ["--solar-radiation", "inf"],
            base + ["--solar-radiation", "178", "--pressure", "nan"],
            [
                "--lat",
                "nan",
                "--lon",
                str(LON),
                "--timestamp",
                str(TS_DAY),
                "--solar-radiation",
                "178",
            ],
        ):
            p = run_cli(*bad)
            self.assertNotEqual(p.returncode, 0, msg=bad)
            self.assertIn("finite", p.stderr)

    def test_rejects_out_of_range(self):
        p = run_cli(
            "--lat",
            "91",
            "--lon",
            str(LON),
            "--timestamp",
            str(TS_DAY),
            "--solar-radiation",
            "178",
        )
        self.assertNotEqual(p.returncode, 0)
        p = run_cli(
            "--lat",
            str(LAT),
            "--lon",
            str(LON),
            "--timestamp",
            str(TS_DAY),
            "--solar-radiation",
            "-5",
        )
        self.assertNotEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
