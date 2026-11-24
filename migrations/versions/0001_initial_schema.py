"""Initial schema: the tables drafted in the PW-4 spike (PW-5).

See docs/spike-openf1.md section 6 and ADR 4 for why the tables look like this.

Revision ID: 0001
Revises:
Create Date: 2026-11-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create every table, in foreign-key order."""
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("session_key", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'running'"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requests", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("rows_written", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "warnings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('running', 'ok', 'partial', 'failed')", name=op.f("ck_ingestion_runs_status")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingestion_runs")),
    )
    op.create_index(
        op.f("ix_ingestion_runs_session_key_started_at"),
        "ingestion_runs",
        ["session_key", "started_at"],
        unique=False,
    )
    op.create_table(
        "meetings",
        sa.Column("meeting_key", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("meeting_name", sa.Text(), nullable=False),
        sa.Column("meeting_official_name", sa.Text(), nullable=True),
        sa.Column("country_code", sa.Text(), nullable=True),
        sa.Column("country_name", sa.Text(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("circuit_key", sa.Integer(), nullable=True),
        sa.Column("circuit_short_name", sa.Text(), nullable=True),
        sa.Column("gmt_offset", sa.Interval(), nullable=True),
        sa.Column("date_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("date_end", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("meeting_key", name=op.f("pk_meetings")),
    )
    op.create_index(op.f("ix_meetings_year"), "meetings", ["year"], unique=False)
    op.create_table(
        "sessions",
        sa.Column("session_key", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("meeting_key", sa.Integer(), nullable=False),
        sa.Column("session_type", sa.Text(), nullable=False),
        sa.Column("session_name", sa.Text(), nullable=False),
        sa.Column("date_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("date_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("load_status", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.CheckConstraint(
            "load_status IN ('pending', 'loaded', 'partial', 'failed')", name=op.f("ck_sessions_load_status")
        ),
        sa.ForeignKeyConstraint(
            ["meeting_key"],
            ["meetings.meeting_key"],
            name=op.f("fk_sessions_meeting_key_meetings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_key", name=op.f("pk_sessions")),
    )
    op.create_index(op.f("ix_sessions_meeting_key"), "sessions", ["meeting_key"], unique=False)
    op.create_table(
        "race_control",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("session_key", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lap_number", sa.Integer(), nullable=True),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("flag", sa.Text(), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("sector", sa.Integer(), nullable=True),
        sa.Column("driver_number", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_key"],
            ["sessions.session_key"],
            name=op.f("fk_race_control_session_key_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_race_control")),
        sa.UniqueConstraint(
            "session_key", "date", "message", name=op.f("uq_race_control_session_key_date_message")
        ),
    )
    op.create_table(
        "safety_car_periods",
        sa.Column("session_key", sa.Integer(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("start_lap", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("end_lap", sa.Integer(), nullable=True),
        sa.CheckConstraint("kind IN ('SC', 'VSC')", name=op.f("ck_safety_car_periods_kind")),
        sa.ForeignKeyConstraint(
            ["session_key"],
            ["sessions.session_key"],
            name=op.f("fk_safety_car_periods_session_key_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_key", "kind", "start_lap", name=op.f("pk_safety_car_periods")),
    )
    op.create_table(
        "session_drivers",
        sa.Column("session_key", sa.Integer(), nullable=False),
        sa.Column("driver_number", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("name_acronym", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("team_name", sa.Text(), nullable=True),
        sa.Column("team_colour", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_key"],
            ["sessions.session_key"],
            name=op.f("fk_session_drivers_session_key_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_key", "driver_number", name=op.f("pk_session_drivers")),
    )
    op.create_table(
        "weather",
        sa.Column("session_key", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("air_temperature", sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column("track_temperature", sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column("humidity", sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column("pressure", sa.Numeric(precision=6, scale=1), nullable=True),
        sa.Column("rainfall", sa.Boolean(), nullable=True),
        sa.Column("wind_speed", sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column("wind_direction", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_key"],
            ["sessions.session_key"],
            name=op.f("fk_weather_session_key_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_key", "date", name=op.f("pk_weather")),
    )
    op.create_table(
        "laps",
        sa.Column("session_key", sa.Integer(), nullable=False),
        sa.Column("driver_number", sa.Integer(), nullable=False),
        sa.Column("lap_number", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("date_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lap_duration", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("sector_1", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("sector_2", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("sector_3", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("i1_speed", sa.Integer(), nullable=True),
        sa.Column("i2_speed", sa.Integer(), nullable=True),
        sa.Column("st_speed", sa.Integer(), nullable=True),
        sa.Column("is_pit_out_lap", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_pit_in_lap", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("stint_number", sa.Integer(), nullable=True),
        sa.Column("tyre_age", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("gap_to_leader_s", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("laps_down", sa.Integer(), nullable=True),
        sa.Column("interval_s", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.CheckConstraint(
            "lap_duration IS NULL OR lap_duration > 0", name=op.f("ck_laps_lap_duration_positive")
        ),
        sa.CheckConstraint("lap_number >= 1", name=op.f("ck_laps_lap_number_positive")),
        sa.ForeignKeyConstraint(
            ["session_key", "driver_number"],
            ["session_drivers.session_key", "session_drivers.driver_number"],
            name=op.f("fk_laps_session_key_driver_number_session_drivers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_key", "driver_number", "lap_number", name=op.f("pk_laps")),
    )
    op.create_index(
        op.f("ix_laps_session_key_lap_number"), "laps", ["session_key", "lap_number"], unique=False
    )
    op.create_table(
        "pit_stops",
        sa.Column("session_key", sa.Integer(), nullable=False),
        sa.Column("driver_number", sa.Integer(), nullable=False),
        sa.Column("lap_number", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stop_duration", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("lane_duration", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_key", "driver_number"],
            ["session_drivers.session_key", "session_drivers.driver_number"],
            name=op.f("fk_pit_stops_session_key_driver_number_session_drivers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_key", "driver_number", "lap_number", name=op.f("pk_pit_stops")),
    )
    op.create_table(
        "session_results",
        sa.Column("session_key", sa.Integer(), nullable=False),
        sa.Column("driver_number", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("points", sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column("number_of_laps", sa.Integer(), nullable=True),
        sa.Column("dnf", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("dns", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("dsq", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("duration_s", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column("gap_to_leader_s", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column("laps_down", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_key", "driver_number"],
            ["session_drivers.session_key", "session_drivers.driver_number"],
            name=op.f("fk_session_results_session_key_driver_number_session_drivers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_key", "driver_number", name=op.f("pk_session_results")),
    )
    op.create_table(
        "starting_grid",
        sa.Column("session_key", sa.Integer(), nullable=False),
        sa.Column("driver_number", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("quali_lap_duration", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_key", "driver_number"],
            ["session_drivers.session_key", "session_drivers.driver_number"],
            name=op.f("fk_starting_grid_session_key_driver_number_session_drivers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_key", "driver_number", name=op.f("pk_starting_grid")),
    )
    op.create_table(
        "stints",
        sa.Column("session_key", sa.Integer(), nullable=False),
        sa.Column("driver_number", sa.Integer(), nullable=False),
        sa.Column("stint_number", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("compound", sa.Text(), nullable=True),
        sa.Column("lap_start", sa.Integer(), nullable=False),
        sa.Column("lap_end", sa.Integer(), nullable=False),
        sa.Column("tyre_age_at_start", sa.Integer(), nullable=True),
        sa.CheckConstraint("lap_end >= lap_start", name=op.f("ck_stints_lap_range")),
        sa.ForeignKeyConstraint(
            ["session_key", "driver_number"],
            ["session_drivers.session_key", "session_drivers.driver_number"],
            name=op.f("fk_stints_session_key_driver_number_session_drivers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_key", "driver_number", "stint_number", name=op.f("pk_stints")),
    )


def downgrade() -> None:
    """Drop every table, in reverse order."""
    op.drop_table("stints")
    op.drop_table("starting_grid")
    op.drop_table("session_results")
    op.drop_table("pit_stops")
    op.drop_index(op.f("ix_laps_session_key_lap_number"), table_name="laps")
    op.drop_table("laps")
    op.drop_table("weather")
    op.drop_table("session_drivers")
    op.drop_table("safety_car_periods")
    op.drop_table("race_control")
    op.drop_index(op.f("ix_sessions_meeting_key"), table_name="sessions")
    op.drop_table("sessions")
    op.drop_index(op.f("ix_meetings_year"), table_name="meetings")
    op.drop_table("meetings")
    op.drop_index(op.f("ix_ingestion_runs_session_key_started_at"), table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
