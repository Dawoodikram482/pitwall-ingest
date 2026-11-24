# pitwall-ingest

[![CI](https://github.com/__GITHUB_OWNER__/pitwall-ingest/actions/workflows/ci.yml/badge.svg)](https://github.com/__GITHUB_OWNER__/pitwall-ingest/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![mypy strict](https://img.shields.io/badge/mypy-strict-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

The ingestion service of [Pit Wall](https://github.com/__GITHUB_OWNER__/agent-avenger), an AI race
strategist for Formula 1. It loads session data (laps, stints, pit stops, weather, race
control, results) from the free [OpenF1](https://openf1.org) API into Postgres, where the
rest of Pit Wall reads it.

## Status

| Story | What | State |
| --- | --- | --- |
| PW-4 | Data spike: what OpenF1 really returns, request budget, source decision, draft schema | Done: [findings](docs/spike-openf1.md) |
| PW-5 onwards | OpenF1 client, Postgres schema, idempotent loader, quality checks | Next |

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

## Project layout

```text
src/pitwall_ingest/
├── api/         HTTP routes: turn requests into service calls
├── services/    Use cases: orchestrate domain logic through ports
├── domain/      Business models and ports (interfaces); depends on nothing else
├── adapters/    Implementations of ports: databases, HTTP clients, clocks
└── __main__.py  Entry point: python -m pitwall_ingest
tests/           Unit and API tests
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

## License

[MIT](LICENSE)
