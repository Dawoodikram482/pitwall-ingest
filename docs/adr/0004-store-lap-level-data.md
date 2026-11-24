# 4. Store lap-level data; reduce time series to one value per lap

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

OpenF1 returns two kinds of data: per-event or per-lap rows (laps, stints, pit stops,
race control), and time series sampled every few seconds (`intervals` about every 4 s per
driver, `position` on every change, car telemetry at about 4 Hz). In the PW-4 spike,
`intervals` alone was 28,131 rows and over 80% of the bytes of one race. The database runs on
a free tier (around 0.5 GB), and every planned strategy question works at lap level:
gaps, undercuts, tyre degradation, pit loss.

## Decision

- Store lap-level and event-level data as returned (cleaned and typed).
- Do **not** store raw `intervals` or `position` rows. During loading, take each driver's
  value at the end of each lap and store it on the lap row: `position`, `gap_to_leader_s`,
  `laps_down` and `interval_s`.
- Do not load car telemetry (`car_data`, `location`) at all, as already decided in the system
  design.
- Derive `is_pit_in_lap`, `stint_number` and `tyre_age` on each lap, and a
  `safety_car_periods` table from race control messages.

## Alternatives considered

- **Store raw intervals:** about 28,000 rows per race, roughly 2.7 million for 2023 to 2026,
  most of the free database for data no tool reads at that resolution.
- **Store raw responses as JSON files and derive later:** needs object storage that is not
  free at this size, and every query would parse JSON.

## Consequences

- The database stays small (about 1,250 lap rows per race) and every tool query hits one
  indexed table.
- Questions that need sub-lap resolution (a gap at the exact moment of an overtake) cannot
  be answered. If one becomes important, intervals can be loaded for that use alone.
- The lap-end derivation is logic that must be tested carefully: a wrong join puts a gap on
  the wrong lap.
