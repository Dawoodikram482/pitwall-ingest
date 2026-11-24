# 3. OpenF1 is the source of session data; Jolpica for the calendar; no FastF1

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Pit Wall needs lap-level data for every session (laps, stints, pit stops, weather, race
control, positions, results) and a calendar to know when to ingest. The project only uses
free sources that need no personal credentials. The system design named three candidates:
OpenF1, FastF1 and Jolpica (the Ergast successor). The PW-4 spike tested them on the
2026 Singapore Grand Prix ([findings](../spike-openf1.md)).

## Decision

- **OpenF1** is the only source of session data, for every session from 2023.
- **Jolpica** provides the season calendar and results before 2023.
- **FastF1 is not used.**

## Alternatives considered

- **FastF1 as the main source or a second source for tyre data:** its timing data now
  comes from F1's live-timing archive, which requires signing in with an F1 account. Without
  one it loads no laps, weather or race control. A personal account in the pipeline breaks
  the "free, no personal credentials" rule and could break whenever F1 changes its login.
  OpenF1 already has everything FastF1 would have added for strategy (compounds, tyre age
  at stint start, pit stop and pit lane times).
- **Mixing sources per table:** adds reconciliation work (driver identities, lap numbering)
  with no data gained.

## Consequences

- One client, one rate limit and one set of quirks to handle in ingestion.
- Data before 2023 is limited to Jolpica's results (no laps or stints). Pit Wall's strategy
  tools therefore cover 2023 onwards.
- If OpenF1 changes its free tier, ingestion stops for new races; the design keeps the
  source behind a port (interface) so a replacement is one adapter.
