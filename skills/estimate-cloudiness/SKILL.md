---
name: estimate-cloudiness
description: >-
  Use when the user asks how cloudy, overcast, sunny, or clear it is right
  now at their WeatherFlow Tempest station — including "is the sun out",
  "how much cloud cover", "is it gray outside", "did it clear up", or why
  solar radiation seems low for the time of day. Scoped to the user's own
  Tempest station and to daylight hours; not a general or regional weather
  service, and not for forecast cloud cover ("will it be cloudy tomorrow").
user-invocable: true
argument-hint: "[question or topic]"
allowed-tools:
  - mcp__plugin_tempest_mcp-server-tempest__tempest_get_stations
  - mcp__plugin_tempest_mcp-server-tempest__tempest_get_observation
  - mcp__plugin_tempest_mcp-server-tempest__tempest_get_forecast
  - Bash(python3:*)
---

Estimate current sky condition at the user's Tempest station by comparing the measured solar radiation to the modeled clear-sky value for that exact place and moment.
The ratio (clearness index) is what carries the signal — an absolute W/m² number means nothing without knowing where the sun is.
Never classify cloudiness from raw solar radiation thresholds alone.

## Workflow

1. Resolve the station with `tempest_get_stations` (single station: use it; multiple: list the station names and ask the user to choose, unless the question already names one).
   Note its `latitude` and `longitude` — the script needs them.
2. Call `tempest_get_observation(station_id, detailed=true)`.
   Detailed mode is required: the concise response omits `station_pressure`.
   Needed fields: `timestamp` (epoch; `observed_at` is the same instant in RFC 3339 UTC), `solar_radiation`, `precip`, and `station_pressure` (or `barometric_pressure` — on Tempest both are the station-level value).
   If `solar_radiation` is absent even in the detailed response, the sensor is not reporting — say so and stop.
   On tool errors, follow the weather-report skill's error-handling rules: retry once when the error's `temporary` flag is true (honoring `retry_after_ms`); otherwise report the failure in plain language.
3. Check freshness: compute the observation's age from its `timestamp` / `observed_at` — a fresh fetch can still return an old last-known reading from an offline station.
   If the observation is more than 10 minutes old, say so — the assessment describes the observation time, not necessarily "now".
   `retrieved_at` is when the server fetched the data upstream; if it is well before the current time, the response came from cache — useful for explaining why data is old (re-fetch with `refresh=true` if the cache is the cause), not for computing the observation's age.
4. Run the bundled script, replacing `$SKILL_DIR` with this skill's base directory (announced when the skill loaded):

   ```bash
   python3 "$SKILL_DIR"/scripts/cloudiness.py \
     --lat 47.641 --lon -122.330 --timestamp 1783040789 \
     --solar-radiation 178 --pressure 1014.9
   ```

   It is stdlib-only and prints one JSON object.
   Prefer `station_pressure` for `--pressure` (observation pressures are always mb, whatever `station_units` says); `sea_level_pressure` or omitting the flag is acceptable (the effect is small).
   `solar_radiation` is always in W/m² regardless of the station's configured units — pass it through unchanged.
5. Interpret the JSON using the rules below and answer in plain language: lead with the verdict, then support it with the clearness index and observed-vs-expected numbers.

## Interpreting the result

Apply these before or alongside the script's category:

- **Rain trumps**: if `precip` > 0 the sky was cloudy at the station at the observation time, whatever the index says — lead with that and use the index only to describe how dark the overcast is.
  Phrase it as "right now" only when the observation passed the freshness check.
- **`status: night`**: cloudiness cannot be measured from solar radiation.
  Say so honestly; if the user still wants an answer, offer the forecast's current conditions via `tempest_get_forecast`, clearly labeled as a model estimate rather than a measurement.
- **`status: sun_too_low`**: same honesty — the sun is too near the horizon for the index to mean anything.

Categories (when `status: ok`):

| category | say something like |
|---|---|
| `clear` | Clear or nearly clear — the sun is unobstructed |
| `sun_and_broken_clouds` | Sunny right now with bright broken clouds — a partly cloudy sky |
| `thin_or_partial` | Ambiguous by nature: thin high clouds or haze, bright overcast, or a moment when a passing cloud covers the sun — name both readings, and use rain/humidity context to lean one way |
| `cloudy` | Mostly cloudy to overcast — the sun is obscured |
| `thick_overcast` | Heavy overcast, heavy rain, or fog |
| `implausible` | Do not report a sky condition — describe an anomalous reading: either a brief extreme cloud-edge enhancement spike or a sensor/data problem (fault, reflection, bad timestamp); suggest re-checking in a few minutes |

- When `confidence` is `low` (sun below ~15°), hedge the verdict and mention that low-angle readings are less reliable.
- Relay any `notes` the script emits when they change what the user should conclude.

## Limits to keep in mind

- This is a single-instant snapshot.
  Under a partly cloudy sky the index swings between high and low minute to minute, so one reading cannot distinguish steady thin overcast from a momentary cloud over the sun — hence the deliberately ambiguous `thin_or_partial` wording.
- The clear-sky model and the sensor each carry roughly 5–10% error, so treat band edges as soft; near a boundary, describe conditions as borderline rather than picking a side.
- `brightness` (lux) is derived from the same sensor as `solar_radiation` (~120 lux per W/m²) and is not independent corroboration; `uv` comes from a separate sensor and can serve as a weak sanity check.
- Trees, buildings, a dirty dome, or snow on the sensor read as cloud.
  If the index seems inconsistent with other signals (e.g., very low index with no rain, low humidity, and high UV), mention possible shading or sensor obstruction.
