# 5. SQLAlchemy 2.0 models and Alembic migrations, checked in CI

- **Status:** Accepted
- **Date:** 2026-11-24

## Context

The ingest service owns the Pit Wall database schema (PW-5). The schema will change as
stories add tables (debriefs, embeddings) and columns. Every change must be reproducible on
a laptop, in CI and on the hosted database, and the Python code must agree with the
database it talks to.

## Decision

- Define the tables once, as typed SQLAlchemy 2.0 models (`adapters/db/models.py`).
- Change the database only through Alembic migrations in `migrations/versions/`, generated
  from the models (`uv run poe migration "..."`) and reviewed like any code.
- A naming convention on the metadata gives every constraint and index a predictable name,
  so later migrations can alter them on every database.
- CI starts a real Postgres 16, applies every migration to an empty database, runs
  `alembic check` (fails if the models and migrations differ), downgrades to empty and
  upgrades again, then runs the constraint tests.
- The Docker image ships the migrations, so a deploy runs `alembic upgrade head` before
  starting the service.

## Alternatives considered

- **Hand-written SQL files:** simple, but nothing keeps the Python models and the schema in
  step; drift shows up at runtime.
- **`metadata.create_all()` at startup:** fine for a demo, but cannot change an existing
  table, so the first schema change would need manual SQL on the hosted database.
- **SQLModel:** less code for simple models, but it hides SQLAlchemy features this schema
  uses (composite foreign keys, check constraints, JSONB) and adds a layer to learn.

## Consequences

- Every schema change is a reviewed file with an upgrade and a downgrade.
- Migrations must be generated, not written by hand from memory; CI catches the ones that
  were forgotten.
- Tests that need a real database run in a separate CI job and are skipped locally unless
  `TEST_DATABASE_URL` points at a throwaway database.
