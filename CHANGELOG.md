# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-11-24

### Added

- Database schema (PW-5): SQLAlchemy 2.0 models for meetings, sessions, session drivers, laps,
  stints, pit stops, race control, safety car periods, weather, results, starting grid and
  ingestion runs, with OpenF1's natural keys as primary keys.
- Alembic with the initial migration; `poe migrate` and `poe migration` tasks.
- `compose.yaml` with Postgres 16, a named volume and a health check; `poe db-up` and `poe db-down`.
- `DATABASE_URL` setting (pydantic-settings) and an engine helper.
- CI job that applies the migrations to a fresh Postgres, runs `alembic check`, downgrades and
  upgrades again, and runs the constraint tests.
- Migrations are included in the Docker image.
- ADR 5: SQLAlchemy 2.0 and Alembic, checked in CI.

## [0.1.0] - 2026-11-22

### Added

- Project created from python-service-template: layered package with a `/health` endpoint,
  uv, ruff, mypy strict, pytest with an 80% coverage gate, pre-commit hooks, Dockerfile and CI.
- Release workflow: merging a new version to main tags it and publishes release notes from this file.
- OpenF1 data spike (PW-4): `notebooks/01-openf1-spike.ipynb`, findings in `docs/spike-openf1.md`,
  ADR 3 (OpenF1 is the session data source) and ADR 4 (store lap-level data).
- nbstripout pre-commit hook, so notebook outputs never reach git.
