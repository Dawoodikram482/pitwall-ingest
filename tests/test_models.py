"""The schema's shape: tables, keys and constraints the loader relies on.

These run without a database. ``test_migrations.py`` checks the same models against a
real Postgres.
"""

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Table, UniqueConstraint

from pitwall_ingest.adapters.db import Base

TABLES = Base.metadata.tables


def primary_key(table: str) -> list[str]:
    return [column.name for column in TABLES[table].primary_key.columns]


def test_every_table_from_the_spike_schema_exists() -> None:
    assert set(TABLES) == {
        "meetings",
        "sessions",
        "session_drivers",
        "laps",
        "stints",
        "pit_stops",
        "race_control",
        "safety_car_periods",
        "weather",
        "session_results",
        "starting_grid",
        "ingestion_runs",
    }


@pytest.mark.parametrize(
    ("table", "key"),
    [
        ("meetings", ["meeting_key"]),
        ("sessions", ["session_key"]),
        ("session_drivers", ["session_key", "driver_number"]),
        ("laps", ["session_key", "driver_number", "lap_number"]),
        ("stints", ["session_key", "driver_number", "stint_number"]),
        ("pit_stops", ["session_key", "driver_number", "lap_number"]),
        ("safety_car_periods", ["session_key", "kind", "start_lap"]),
        ("weather", ["session_key", "date"]),
        ("session_results", ["session_key", "driver_number"]),
        ("starting_grid", ["session_key", "driver_number"]),
    ],
)
def test_primary_keys_are_the_upsert_keys(table: str, key: list[str]) -> None:
    assert primary_key(table) == key


def test_race_control_upserts_on_time_and_message() -> None:
    uniques = [c for c in TABLES["race_control"].constraints if isinstance(c, UniqueConstraint)]

    assert [[col.name for col in u.columns] for u in uniques] == [["session_key", "date", "message"]]


def test_laps_are_indexed_for_per_lap_queries() -> None:
    indexes = {index.name: [col.name for col in index.columns] for index in TABLES["laps"].indexes}

    assert indexes == {"ix_laps_session_key_lap_number": ["session_key", "lap_number"]}


@pytest.mark.parametrize("table", ["laps", "stints", "pit_stops", "session_results", "starting_grid"])
def test_per_driver_tables_reference_session_drivers(table: str) -> None:
    fks = [c for c in TABLES[table].constraints if isinstance(c, ForeignKeyConstraint)]

    assert len(fks) == 1
    assert fks[0].referred_table.name == "session_drivers"
    assert fks[0].ondelete == "CASCADE"


def test_ingestion_runs_survive_deleting_a_session() -> None:
    assert not TABLES["ingestion_runs"].foreign_keys


def check_names(table: Table) -> set[str]:
    return {str(c.name) for c in table.constraints if isinstance(c, CheckConstraint)}


def test_check_constraints_have_predictable_names() -> None:
    assert check_names(TABLES["laps"]) == {
        "ck_laps_lap_number_positive",
        "ck_laps_lap_duration_positive",
    }
    assert check_names(TABLES["sessions"]) == {"ck_sessions_load_status"}
    assert check_names(TABLES["ingestion_runs"]) == {"ck_ingestion_runs_status"}
    assert check_names(TABLES["safety_car_periods"]) == {"ck_safety_car_periods_kind"}
