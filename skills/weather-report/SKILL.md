---
name: weather-report
description: >-
  Use when the user asks about current weather, short-term forecast, outdoor
  conditions, or weather-related decisions using data from their WeatherFlow
  Tempest station. Triggers include current conditions, rain chances,
  clothing/comfort questions, wind conditions, rain timing, gardening or
  frost risk, spray safety, lightning,
  trail drying, solar conditions, pressure changes, and activity suitability
  such as running or drone flying. Scoped to the user's own Tempest station;
  not a general or regional weather service.
user-invocable: true
argument-hint: "[question or topic]"
allowed-tools:
  - mcp__plugin_tempest_mcp-server-tempest__tempest_get_stations
  - mcp__plugin_tempest_mcp-server-tempest__tempest_get_observation
  - mcp__plugin_tempest_mcp-server-tempest__tempest_get_forecast
  - mcp__plugin_tempest_mcp-server-tempest__tempest_get_station_details
  - mcp__plugin_tempest_mcp-server-tempest__tempest_get_capabilities
  - ReadMcpResourceTool
  - WebSearch
---

Answer weather questions using data from the user's WeatherFlow Tempest personal weather station.
Use the MCP tools to retrieve real-time observations, forecasts, and station metadata.
Use WebSearch only to supplement station data with seasonal norms, historical records, or regional context — not as a primary source.

## Workflow

1. **Resolve the station**: Call `tempest_get_stations`.
   - If one station is returned, use it.
   - If multiple are returned and the question doesn't name one, list the station names and ask the user to choose — the station list carries no activity timestamp to pick by.
   - For "what can my station measure", read `station_items` from `tempest_get_stations` — it lists the sensors each station reports.
     Call `tempest_get_station_details` only if you also need each sensor's indoor/outdoor environment (its `capabilities` list); otherwise it repeats the `tempest_get_stations` entry.
   - If no stations are found, stop and tell the user their account has no Tempest stations configured.

2. **Fetch only what the question requires**:
   - Current conditions only → `tempest_get_observation` alone is sufficient.
   - Forecast or trend questions → also call `tempest_get_forecast`.
     Pass explicit `hours` / `days` to set depth — they are honored in both summary and detailed modes.
     When `hours` / `days` are omitted, the response defaults to 6 hourly and 2 daily entries.
     `detailed=true` changes field density only, never the entry count.
     **Check the response's `truncated` flag and `truncation_hint`** (alongside `requested_*` / `returned_*`) to detect an upstream shortfall before telling the user a range is complete.
   - Derived/comfort metrics (WBGT, delta-T, wet bulb, heat index, wind chill, air density) → pass `detailed=true` to `tempest_get_observation` whenever the answer needs one, whether or not the user names it (e.g. delta-T for spray safety).
     The concise (default) observation omits them.
     `detailed=true` on `tempest_get_forecast` does not add these metrics — it only keeps null fields and adds station coordinates.
     The forecast's `current_conditions` carries `feels_like` and, when upstream supplies it, `wet_bulb_temperature`.
   - To present values in the owner's preferred units you need `station_units`, which only `tempest_get_observation` returns.
     For a forecast-only question, also call `tempest_get_observation` (it is light) unless you already hold `station_units` for this station.
   - Pass `refresh=true` to `tempest_get_observation` or `tempest_get_forecast` only when the user needs the latest reading (e.g. "right now" during fast-changing conditions) or a cached result is too old; otherwise accept cached data (up to 5 minutes by default).

3. **Check data quality before answering** (see Data Quality below).

4. **Classify the question and apply the appropriate section below** — most questions fit one or two sections.
   Don't run all analyses for every question.

5. **Respond** following the Output rules below.

## Output

These apply to every response, whichever analysis sections you used:

- Respond in plain language.
  Translate raw fields into described values, not raw numbers alone.
- **Read every value in the units named by that result's own `units` object.**
  Observation values are always metric/SI (°C, m/s, mb, mm, km) regardless of the station's settings; forecast values follow the forecast result's `units`.
  `station_units` is only the owner's display preference, never the units of the values.
- Report in the owner's preferred units from `station_units`, converting as needed (e.g. `wind_avg: 2.5` with `units_wind: mps` → "light breeze around 6 mph" when `station_units.units_wind` is `mph`).
  If the user requests a different unit system, use that instead.
- For casual questions like "do I need a jacket?" or "is it good for a run?", give a direct, conversational answer first, back it up with the relevant data points, and add practical advice when it changes what the user should do (gear, timing, route).

## Time & Place

Station data describes one place at one time — reason about both explicitly:

- All time-of-day and calendar reasoning ("this morning", "tonight", "tomorrow") uses the station's timezone (`timezone` in `tempest_get_stations`), with day boundaries at station-local midnight — never the agent's or session's locale.
  Hourly forecast entries carry `local_day` and `local_hour`, which are already station-local.
- Forecast times come with RFC 3339 UTC twins of their epoch fields: `sunrise_at`, `sunset_at`, and `day_start_at` on daily entries, `starts_at` on hourly entries, and `observed_at` on `current_conditions`.
  Convert them to the station's `timezone` before stating a clock time ("sunset at 6:56pm").
- Do not assert time of day unless you know the current time from a trustworthy source (the session's current date/time), converted to the station's timezone.
  The observation `observed_at` (RFC 3339 UTC; same instant as the epoch `timestamp`) is when the reading was taken, not "now" — use it for time-of-day only when the data is fresh (see Data Quality); a stale observation's timestamp is the past.
  Low solar radiation or UV reflects cloud cover, not necessarily dusk, and is never evidence of the time.
- Prefer absolute station-local times ("by 4pm") over relative ones ("in 3 hours"), especially when the data may be stale.
- Readings describe conditions at the station's location at measurement time.
  The user or agent may be somewhere else entirely (travel, scheduled or cloud execution) — never phrase observations as the user's surroundings unless they have said they are at the station.
- Name the station or its location in the answer whenever there is any chance of ambiguity; always when the account has multiple stations.
- Lightning distances are measured from the station, not from the user.
- If the user asks about a location other than the station's, say the station cannot answer for that place rather than substituting station data.

## Data Quality

Before interpreting sensor values, check:

- **Stale data**: **If the observation is more than 10 minutes old, say so before answering.**
  Compute the age from the observation's own `observed_at` (or `timestamp`) — a fresh fetch can still return an old last-known reading from an offline station, so `retrieved_at` alone can make stale data look current.
  `retrieved_at` (RFC 3339 UTC, in every fetching result) is when the data was fetched upstream; compare it with the current time to see how long the result has been served from cache.
  Use it to tell the user why data is old, and re-fetch with `refresh=true` if a cached result is the problem.
  If your client shows result `_meta`, `_meta["net.bconnelly.tempest/fetch"].cache` also names the source (`miss`, `memory`, or `disk`); many clients do not, so never depend on it.
- **Missing or null fields**: Concise (default) responses omit null-valued optional fields, so an absent field is not an error.
  Some metrics (WBGT, delta-T, air density) are only computed under certain conditions.
  If a metric you need is missing from an observation, re-fetch it with `detailed=true`; if it is still null, skip it rather than reporting "null."
- **Implausible values**: A temperature of −50°C or UV of 30 likely indicates a sensor fault.
  Note the anomaly rather than interpreting the value literally.
- **Forecast vs. observation disagreement**: If current conditions and the forecast's current snapshot differ substantially, prefer the observation and note the discrepancy.

## Handling Tool Errors

When a tool call fails, the server returns an error result instead of weather data: a flat JSON object carrying a `code`, a human-readable `message`, a boolean `temporary` flag, and a `request_id`, plus optional `hint`, `field`, `value`, `repair`, `retry_after_ms`, and `details`.
When `repair` is present, it is a ready-made retry: call `repair.tool` with `repair.arguments` exactly.
Translate it into plain language for the user — never surface the raw JSON.
Act on the `code`:

- `auth_missing`, `auth_invalid`, `auth_forbidden`: the `WEATHERFLOW_API_TOKEN` is missing, wrong, or lacks access.
  Not retryable — tell the user to check their token configuration.
- `invalid_argument`: a malformed argument was sent.
  `field` names the offending parameter (an unrecognized argument is named in `details.unknown_argument` instead); follow `repair` to retry once, or correct the call yourself if no `repair` is present.
- `station_not_found`: the station id is unknown.
  Re-resolve with `tempest_get_stations` (its `repair` points there) rather than retrying the same id.
- `rate_limited`, `upstream_unavailable`: `temporary` is true.
  Back off briefly (honor `retry_after_ms` if present), retry once, and if it still fails tell the user the service is briefly unavailable and to try again shortly.
- `upstream_invalid_response`, `internal_error`: not retryable.
  Report that the data couldn't be retrieved, and include the `request_id` if the user wants to follow up.

## Server Capabilities

The server exposes a machine-readable `tempest://capabilities` resource (also available as the `tempest_get_capabilities` tool, for clients that surface MCP resources poorly) summarizing the available tools, error codes, station scope, units and timestamp conventions, and a surface `fingerprint` — the same value that appears in every result's `_meta["net.bconnelly.tempest/fetch"].fingerprint` when your client shows `_meta` (compare `fingerprint_contract_version` too: a change there means the fingerprint is measured differently, not that the surface changed).
When a tool's name or behavior disagrees with these instructions, consult it — a server upgrade is the usual cause.
Otherwise you don't need it.

## Weather Briefing

When producing a general briefing or when no specific question is asked:

- Summarize current conditions: temperature, humidity, wind, pressure, precipitation, UV index
- Highlight the forecast outlook for the next 12–24 hours
- Call out anything notable: incoming storms, temperature swings, high UV, frost risk, etc.

## Best Activity Window

When the user asks when to do an activity ("when should I run today?", "best time to mow the lawn?"):

- Fetch the hourly forecast with explicit `hours` covering the asked horizon; when none is stated, cover the rest of the station-local day (`hours=24` always reaches it; keep entries whose `local_day` is today).
- Rank hours on the dimensions the activity cares about: `precip_probability`, `feels_like`, `wind_avg` / `wind_gust`, and `uv`.
- Recommend one or two windows with reasons, in station-local times ("6–8pm: dry, light wind, cooling to 18°C").
  Hourly entries carry `local_hour` / `local_day`, already in the station's timezone.
- If no window is acceptable, say so plainly and name the least-bad option instead of forcing a recommendation.

## Alerts & Anomalies

Scan only the data already retrieved for the question — do not fetch additional data solely to look for anomalies.
Proactively flag these when present:

- Barometric pressure trending falling (potential storm approaching) or rising (clearing likely)
- Lightning activity or strikes detected
- High UV index (6+)
- Extreme temperatures for the season (use WebSearch to retrieve local historical norms if needed to confirm the deviation is significant)
- High wind gusts
- Heavy or prolonged precipitation
- Sensor anomalies (missing data, unreasonable values)

## Trend Analysis

When the user asks about trends or changes:

- Compare the current observation to the forecast's current snapshot to infer direction
- Identify patterns: rising/falling pressure, temperature trends, wind shifts
- Note rapid changes that might indicate incoming weather fronts
- The API provides no time-series history, so note that recent trends are estimated from the current pressure trend and short-range forecast rather than measured history
- Describe trends in plain language with supporting data

## Comfort & Heat Stress

Interpret derived comfort metrics rather than listing raw numbers:

- **Wet Bulb Globe Temperature (WBGT)**: Accounts for heat, humidity, wind, and sun exposure.
  Below 25°C: low risk. 25–28°C: moderate (take breaks, hydrate). 28–30°C: high (limit strenuous activity). Above 30°C: dangerous.
- **Dew point comfort**: Below 10°C (50°F) is dry. 10–16°C (50–60°F) is pleasant. 16–18°C (60–65°F) is sticky. Above 18°C (65°F) is muggy. Above 21°C (70°F) is oppressive.

## Feels Like Temperature

The station reports `feels_like`, `wind_chill`, and `heat_index`.
Choose the right metric:

- **Wind chill** is meaningful only when temperature is below 10°C (50°F) and wind is above 3 mph. Otherwise it equals air temperature.
- **Heat index** is meaningful only when temperature is above 27°C (80°F) and humidity is above 40%. Otherwise it equals air temperature.
- When neither applies, report the actual temperature.
  Do not call out "feels like" as a separate value.

Only call out feels-like when it meaningfully differs from actual air temperature (at least 2°C / 4°F).

## Wind Interpretation

Describe wind rather than quoting raw numbers.
Thresholds below are sustained `wind_avg` in mph / km/h; convert from the result's `units.units_wind` (observations are always m/s) first:

- **Calm**: below 1 mph / 2 km/h.
- **Light**: 1–7 mph / 2–11 km/h.
- **Moderate**: 8–18 mph / 12–29 km/h.
- **Fresh**: 19–24 mph / 30–39 km/h.
- **Strong**: 25–38 mph / 40–61 km/h.
- **Gale**: 39+ mph / 62+ km/h.

Also:

- **Gust factor**: when `wind_avg` is at least 3 mph / 5 km/h and `wind_gust` is at least twice `wind_avg`, describe conditions as gusty; below that floor, describe the wind as calm or light without gust framing.
  Call it out when it changes advice — drone flying, cycling, spray drift.
- **Direction**: use the server-provided 16-point `wind_direction_cardinal` (on observations, forecast entries, and the forecast's current snapshot) rather than converting `wind_direction` degrees yourself.
  Mention direction when it matters to the activity or signals a shift (see Trend Analysis), not on every answer.

## Pressure-Based Forecasting

Go beyond reporting the `pressure_trend` value (`falling`, `steady`, or `rising`).
The server exposes no pressure history, so a rate of change cannot be computed — interpret the categorical trend together with the current sea-level pressure and the short-range forecast.
Pressure values below are in mb (≡ hPa), which is what observations return.
If a result's `units.units_pressure` is `inhg`, multiply by 33.864.

These are estimates — local topography, season, and frontal structure affect reliability.
Present as likely outcomes, not certainties.

- **Falling, sea-level pressure above 1010 mb**: Conditions likely changing; check the forecast for rain or wind in the next 6–12 hours and lead with it.
- **Falling, sea-level pressure at or below 1010 mb**: Front likely approaching; conditions may deteriorate within hours.
- **Rising**: Clearing likely; improving conditions ahead.
- **Steady at 1020+ mb**: Fair weather likely to persist.
- **Steady between 1000 and 1020 mb**: No strong pressure signal; rely on the forecast.
- **Steady below 1000 mb**: Unsettled conditions likely to continue.

(Falling and rising pressure trends are on the Alerts & Anomalies proactive-flag list.)

## Gardening & Frost Guidance

Include the guidance below when the user asks about gardening, plants, or yard work, or when a briefing surfaces frost risk, spray-relevant conditions, or significant recent or forecast rain:

- **Frost risk**: Flag when overnight lows are forecast at or below 2°C (36°F).
  Advise covering or bringing in sensitive plants.
- **Watering guidance**: If measurable precipitation fell in the last 24 hours (`precip_accum_local_day` or `precip_accum_local_yesterday_final`) or rain is forecast at 50%+ probability in the next 24 hours, suggest skipping manual watering.
- **Spray safety**: Delta-T between 2–8°C and wind below 10 mph are ideal for pesticide/herbicide application.
  Below 2°C: droplets won't evaporate properly.
  8–10°C: marginal — evaporation losses increase, so prefer the cooler parts of the day.
  Above 10°C: too much evaporation and drift risk.
- **UV stress**: UV index 6+ is strong enough to stress transplants and light-skinned fruit.

## Lightning Risk Assessment

Use `lightning_strike_count`, `lightning_strike_count_last_1hr`, `lightning_strike_count_last_3hr`, `lightning_strike_last_distance` (in the result's `units.units_distance`; km for observations), and `lightning_strike_last_at`:

- **No risk**: Zero strikes in the last 3 hours.
- **Distant activity**: Strikes detected but >30 km away.
  Worth monitoring.
- **Approaching threat**: Strikes 15–30 km away, especially if count is increasing or distance decreasing.
  Advise caution outdoors.
- **Immediate danger**: Strikes closer than 15 km.
  Advise seeking shelter immediately — avoid open areas, water, tall isolated objects, and metal structures.

Check `lightning_strike_last_at` (RFC 3339 UTC; epoch in `lightning_strike_last_epoch`) against the current time.
Strikes more than a few hours old are historical.
Use 1-hour and 3-hour counts to judge whether activity is ongoing.

(Detected lightning is on the Alerts & Anomalies proactive-flag list.)

## Rain Timing

When the user asks when rain starts or stops, or how long it will last:

- If the current observation shows active precipitation, lead with that; use the forecast only for the taper.
- Read hourly `precip_probability` and use tiered language: below 30% unlikely, 30–60% possible, above 60% likely.
- Report onset and offset as station-local time ranges ("likely starting mid-afternoon, tapering after 8pm"), not exact minutes — forecast resolution is hourly.
- Mention the forecast `precip_type` when it is not plain rain (see Precipitation Type Inference for observation-based inference).

## Precipitation Type Inference

The station reports precipitation rate but not type.
Infer from wet bulb temperature.
These thresholds are estimates; vertical temperature structure and local elevation can shift the boundaries.

- **Wet bulb below −1°C (30°F)**: Almost certainly snow.
- **Wet bulb −1°C to 1.5°C (30–35°F)**: Mixed zone — sleet, freezing rain, or wet snow possible. Flag the ambiguity.
- **Wet bulb above 1.5°C (35°F)**: Rain.
- **Air temperature below 0°C with wet bulb near 0°C**: Freezing rain risk — warn about icy surfaces even if precipitation is light.

Mention inferred precipitation type only when precipitation is occurring and the air temperature is at or below 3°C (37°F).

## Drying Conditions

Combine delta-T, wind, and solar radiation to assess surface drying time.
Useful for outdoor projects, trail conditions, or post-rain timing:

- **Fast drying**: Delta-T above 6°C, wind above 10 mph, solar radiation above 400 W/m².
  Surfaces dry within a few hours.
- **Moderate drying**: Delta-T 3–6°C, light wind, or moderate solar.
  Allow half a day or more.
- **Slow drying**: Delta-T below 3°C, calm wind, overcast (solar below 200 W/m²).
  Surfaces may stay wet all day; trails will be muddy.

## Air Density & Performance

`air_density` in kg/m³; sea-level standard is ~1.225 kg/m³:

- **Below 1.15 kg/m³**: Thin air — reduced engine performance, less drone lift, balls travel farther.
- **1.15–1.30 kg/m³**: Normal range.
- **Above 1.30 kg/m³**: Dense air — better engine performance, more drone lift, balls travel shorter.

Mention air density only when the user asks about sports performance, drone flying, or engine/vehicle performance, or when the value is notably outside normal range.

## Solar Radiation

`solar_radiation` in W/m², for solar-energy and exposure questions:

- **Above 800 W/m²**: Strong — excellent solar production, sunburn risk with prolonged exposure.
- **400–800 W/m²**: Moderate — decent solar output.
- **200–400 W/m²**: Weak — limited solar energy.
- **Below 200 W/m²**: Very low output.

Do not classify sky condition (clear, partly cloudy, overcast) from raw W/m² — the same value can mean overcast at midday or clear sky near sunset.
For "how cloudy/sunny is it" questions, use the tempest estimate-cloudiness skill, which compares the reading against the modeled clear-sky value for the station's location and time.

Mention solar radiation when the user asks about solar energy, outdoor photography, or UV exposure context.
