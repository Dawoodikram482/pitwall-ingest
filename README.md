# pitwall-ingest

[![CI](https://github.com/Dawoodikram482/pitwall-ingest/actions/workflows/ci.yml/badge.svg)](https://github.com/Dawoodikram482/pitwall-ingest/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![mypy strict](https://img.shields.io/badge/mypy-strict-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

The ingestion service of [Pit Wall](https://github.com/Dawoodikram482/agent-avenger), an AI race
strategist for Formula 1. It loads session data (laps, stints, pit stops, weather, race
control, results) from the free [OpenF1](https://openf1.org) API into Postgres, where the
rest of Pit Wall reads it.

## Status

| Story | What | State |
| --- | --- | --- |
| PW-4 | Data spike: what OpenF1 really returns, request budget, source decision, draft schema | Done: [findings](docs/spike-openf1.md) |
| PW-5 | Database schema: SQLAlchemy models, Alembic migrations, local Postgres, CI checks | Done |
| PW-6, PW-7 | OpenF1 client, idempotent loader, data-quality checks | Next |

## Data sources

| Source | Used for | Notes |
| --- | --- | --- |
| [OpenF1](https://openf1.org) | Every session from 2023: laps, stints, pit stops, weather, race control, positions, gaps, results | Free, no key; 3 requests/s and 30/min ([ADR 3](docs/adr/0003-openf1-is-the-session-data-source.md)) |
| [Jolpica](https://github.com/jolpica/jolpica-f1) (Ergast successor) | Season calendar; results before 2023 | Free, no key |

FastF1 is not used: loading timing data now needs a personal F1 account (see the spike).

## Quickstart

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/). uv installs Python 3.12 itself if needed.

```bash
uv sync              # create .venv with all dependencies
uv run poe check     # lint, type check and tests
uv run poe run       # start the service on http://127.0.0.1:8000
```

Then open <http://127.0.0.1:8000/health> or the API docs at <http://127.0.0.1:8000/docs>.

With Docker:

```bash
docker build -t pitwall-ingest .
docker run --rm -p 8000:8000 pitwall-ingest
```

## Database

Postgres 16. The tables follow the spike's schema ([section 6](docs/spike-openf1.md#6-draft-schema)):
`meetings`, `sessions`, `session_drivers`, `laps`, `stints`, `pit_stops`, `race_control`,
`safety_car_periods`, `weather`, `session_results`, `starting_grid` and `ingestion_runs`.
Primary keys are OpenF1's natural keys, so reloading a session updates rows instead of
duplicating them.

```bash
cp .env.example .env          # DATABASE_URL already points at the compose database
uv run poe db-up              # Postgres in Docker, waits until healthy
uv run poe migrate            # alembic upgrade head
```

Changing the schema: edit `src/pitwall_ingest/adapters/db/models.py`, then
`uv run poe migration "what changed"`, review the generated file in `migrations/versions/`,
and run `uv run poe migrate`. CI fails if the models and migrations differ ([ADR 5](docs/adr/0005-sqlalchemy-and-alembic.md)).

The migration tests need an **empty throwaway** database, because every test wipes it:

```bash
docker compose exec db createdb -U pitwall pitwall_test
TEST_DATABASE_URL=postgresql+psycopg://pitwall:pitwall@localhost:5432/pitwall_test uv run pytest -m postgres
```

Without `TEST_DATABASE_URL` those tests are skipped, so `uv run poe check` works without Docker.

## Notebooks

Spikes and data exploration live in `notebooks/`. Their packages are in a separate group,
so the service and CI do not install them:

```bash
uv sync --group notebook
uv run poe notebook      # opens Jupyter Lab; or open the .ipynb in VS Code
```

Outputs are stripped on every commit by the nbstripout pre-commit hook.

## Tasks

Run `uv run poe` to list them.

| Task | What it does |
| --- | --- |
| `uv run poe check` | Everything CI runs: lint, type check, tests |
| `uv run poe lint` | ruff lint and format check |
| `uv run poe format` | Fix lint issues and format the code |
| `uv run poe typecheck` | mypy --strict on `src`, `tests` and `scripts` |
| `uv run poe test` | pytest with coverage |
| `uv run poe run` | Start the service |
| `uv run poe dev` | Start with auto-reload |
| `uv run poe hooks` | Install the pre-commit hooks |
| `uv run poe db-up` / `db-down` | Start or stop the local Postgres |
| `uv run poe migrate` | Apply all migrations |
| `uv run poe migration "msg"` | Generate a migration from model changes |
| `uv run poe notebook` | Open the notebooks in Jupyter Lab |

## Project layout

```text
src/pitwall_ingest/
├── api/         HTTP routes: turn requests into service calls
├── services/    Use cases: orchestrate domain logic through ports
├── domain/      Business models and ports (interfaces); depends on nothing else
├── adapters/    Implementations of ports: databases, HTTP clients, clocks
└── __main__.py  Entry point: python -m pitwall_ingest
tests/           Unit and API tests
notebooks/       Spikes and data exploration (outputs stripped)
migrations/      Alembic migrations (versions/0001_initial_schema.py, ...)
compose.yaml     Local Postgres
docs/adr/        Architecture decision records
```

Dependencies point inward: `api → services → domain ← adapters`. Services depend on
ports, not on adapters, so tests swap in fakes (see `FakeClock` in `tests/conftest.py`).

## Configuration

Copy `.env.example` to `.env` and adjust. `.env` is git-ignored.

| Variable | Default | Meaning |
| --- | --- | --- |
| `HOST` | `127.0.0.1` (Docker: `0.0.0.0`) | Address the server binds to |
| `PORT` | `8000` | Port the server listens on |

## Design decisions

- [ADR 1: Record architecture decisions](docs/adr/0001-record-architecture-decisions.md)
- [ADR 2: Use poethepoet as the task runner](docs/adr/0002-poethepoet-task-runner.md)
- [ADR 3: OpenF1 is the source of session data; Jolpica for the calendar; no FastF1](docs/adr/0003-openf1-is-the-session-data-source.md)
- [ADR 4: Store lap-level data; reduce time series to one value per lap](docs/adr/0004-store-lap-level-data.md)
- [ADR 5: SQLAlchemy 2.0 models and Alembic migrations, checked in CI](docs/adr/0005-sqlalchemy-and-alembic.md)

## License

[MIT](LICENSE)
