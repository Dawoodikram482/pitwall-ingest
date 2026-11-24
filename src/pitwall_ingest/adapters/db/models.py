"""SQLAlchemy models for the Pit Wall database.

The tables follow the schema drafted in the PW-4 spike (``docs/spike-openf1.md``, section 6):

- Keys follow OpenF1, so a reload upserts onto the same rows (idempotent loading).
- Lap-level data only: ``intervals`` and ``position`` are reduced to one value per lap and
  stored on ``laps`` (ADR 4).
- Columns marked *derived* are computed by the loader, not returned by OpenF1 directly.

Migrations in ``migrations/`` must match these models; CI fails if they drift
(``alembic check``).
"""

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    Interval,
    MetaData,
    Numeric,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Predictable constraint names, so migrations can refer to them on every database.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Seconds with millisecond precision: lap and sector times, pit times, gaps.
Seconds = Numeric(8, 3)
# Longer durations: a whole race is about 6,000 s.
LongSeconds = Numeric(10, 3)
UtcTime = DateTime(timezone=True)

LOAD_STATUSES = ("pending", "loaded", "partial", "failed")
RUN_STATUSES = ("running", "ok", "partial", "failed")
SAFETY_CAR_KINDS = ("SC", "VSC")


def _one_of(column: str, values: tuple[str, ...]) -> str:
    """SQL for ``column IN (...)``, used in check constraints."""
    quoted = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({quoted})"


def _driver_fk() -> ForeignKeyConstraint:
    """Composite foreign key from a per-driver table to ``session_drivers``."""
    return ForeignKeyConstraint(
        ["session_key", "driver_number"],
        ["session_drivers.session_key", "session_drivers.driver_number"],
        ondelete="CASCADE",
    )


def _session_fk() -> ForeignKey:
    """Foreign key column to ``sessions``; deleting a session deletes its data."""
    return ForeignKey("sessions.session_key", ondelete="CASCADE")


class Base(DeclarativeBase):
    """Base class of every model; carries the naming convention."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Meeting(Base):
    """A race weekend, e.g. the 2026 Singapore Grand Prix (OpenF1 ``meetings``)."""

    __tablename__ = "meetings"

    meeting_key: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    year: Mapped[int] = mapped_column(Integer)
    meeting_name: Mapped[str] = mapped_column(Text)
    meeting_official_name: Mapped[str | None] = mapped_column(Text)
    country_code: Mapped[str | None] = mapped_column(Text)
    country_name: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    circuit_key: Mapped[int | None] = mapped_column(Integer)
    circuit_short_name: Mapped[str | None] = mapped_column(Text)
    gmt_offset: Mapped[timedelta | None] = mapped_column(Interval)
    date_start: Mapped[datetime] = mapped_column(UtcTime)
    date_end: Mapped[datetime | None] = mapped_column(UtcTime)

    __table_args__ = (Index(None, "year"),)


class Session(Base):
    """One practice, qualifying, sprint or race session (OpenF1 ``sessions``)."""

    __tablename__ = "sessions"

    session_key: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    meeting_key: Mapped[int] = mapped_column(ForeignKey("meetings.meeting_key", ondelete="CASCADE"))
    session_type: Mapped[str] = mapped_column(Text)
    session_name: Mapped[str] = mapped_column(Text)
    date_start: Mapped[datetime] = mapped_column(UtcTime)
    date_end: Mapped[datetime | None] = mapped_column(UtcTime)
    load_status: Mapped[str] = mapped_column(Text, server_default=text("'pending'"))
    """pending, loaded, partial (loaded with data-quality warnings) or failed."""

    __table_args__ = (
        CheckConstraint(_one_of("load_status", LOAD_STATUSES), name="load_status"),
        Index(None, "meeting_key"),
    )


class SessionDriver(Base):
    """A driver in one session, with the team they drove for (OpenF1 ``drivers``).

    Stored per session because numbers and teams change between seasons.
    """

    __tablename__ = "session_drivers"

    session_key: Mapped[int] = mapped_column(_session_fk(), primary_key=True)
    driver_number: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name_acronym: Mapped[str] = mapped_column(Text)
    full_name: Mapped[str] = mapped_column(Text)
    team_name: Mapped[str | None] = mapped_column(Text)
    team_colour: Mapped[str | None] = mapped_column(Text)


class Lap(Base):
    """One lap by one driver (OpenF1 ``laps``, plus values derived per lap)."""

    __tablename__ = "laps"

    session_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    lap_number: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    date_start: Mapped[datetime | None] = mapped_column(UtcTime)
    lap_duration: Mapped[Decimal | None] = mapped_column(Seconds)
    """Null on the lap a driver retired on."""
    sector_1: Mapped[Decimal | None] = mapped_column(Seconds)
    sector_2: Mapped[Decimal | None] = mapped_column(Seconds)
    sector_3: Mapped[Decimal | None] = mapped_column(Seconds)
    i1_speed: Mapped[int | None] = mapped_column(Integer)
    i2_speed: Mapped[int | None] = mapped_column(Integer)
    st_speed: Mapped[int | None] = mapped_column(Integer)
    is_pit_out_lap: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    is_pit_in_lap: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    """Derived: the lap before a pit-out lap."""
    stint_number: Mapped[int | None] = mapped_column(Integer)
    """Derived from ``stints``; null when no stint covers the lap (retirement lap)."""
    tyre_age: Mapped[int | None] = mapped_column(Integer)
    """Derived: tyre age at stint start plus laps into the stint."""
    position: Mapped[int | None] = mapped_column(Integer)
    """Derived: position at the end of the lap."""
    gap_to_leader_s: Mapped[Decimal | None] = mapped_column(Seconds)
    """Derived: gap to the leader at the end of the lap; null when lapped."""
    laps_down: Mapped[int | None] = mapped_column(Integer)
    """Derived: laps behind the leader (0 on the lead lap)."""
    interval_s: Mapped[Decimal | None] = mapped_column(Seconds)
    """Derived: gap to the car ahead at the end of the lap."""

    __table_args__ = (
        _driver_fk(),
        CheckConstraint("lap_number >= 1", name="lap_number_positive"),
        CheckConstraint("lap_duration IS NULL OR lap_duration > 0", name="lap_duration_positive"),
        # "Every driver on lap N" queries; (session, driver, lap) is the primary key index.
        Index(None, "session_key", "lap_number"),
    )


class Stint(Base):
    """A run on one set of tyres (OpenF1 ``stints``)."""

    __tablename__ = "stints"

    session_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    stint_number: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    compound: Mapped[str | None] = mapped_column(Text)
    lap_start: Mapped[int] = mapped_column(Integer)
    lap_end: Mapped[int] = mapped_column(Integer)
    tyre_age_at_start: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        _driver_fk(),
        CheckConstraint("lap_end >= lap_start", name="lap_range"),
    )


class PitStop(Base):
    """A pit stop (OpenF1 ``pit``)."""

    __tablename__ = "pit_stops"

    session_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    lap_number: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    date: Mapped[datetime] = mapped_column(UtcTime)
    stop_duration: Mapped[Decimal | None] = mapped_column(Seconds)
    """Time stationary in the box."""
    lane_duration: Mapped[Decimal | None] = mapped_column(Seconds)
    """Whole pit lane, entry to exit (OpenF1 ``lane_duration`` = ``pit_duration``)."""

    __table_args__ = (_driver_fk(),)


class RaceControlMessage(Base):
    """A race control message: flags, safety car, penalties (OpenF1 ``race_control``)."""

    __tablename__ = "race_control"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    session_key: Mapped[int] = mapped_column(_session_fk())
    date: Mapped[datetime] = mapped_column(UtcTime)
    lap_number: Mapped[int | None] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(Text)
    flag: Mapped[str | None] = mapped_column(Text)
    scope: Mapped[str | None] = mapped_column(Text)
    sector: Mapped[int | None] = mapped_column(Integer)
    driver_number: Mapped[int | None] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text)

    # OpenF1 has no message id; time plus text identifies a message for upserts.
    __table_args__ = (UniqueConstraint("session_key", "date", "message"),)


class SafetyCarPeriod(Base):
    """Derived: a safety car or virtual safety car period, from race control messages."""

    __tablename__ = "safety_car_periods"

    session_key: Mapped[int] = mapped_column(_session_fk(), primary_key=True)
    kind: Mapped[str] = mapped_column(Text, primary_key=True)
    start_lap: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    end_lap: Mapped[int | None] = mapped_column(Integer)
    """Null if the session ended under the safety car."""

    __table_args__ = (CheckConstraint(_one_of("kind", SAFETY_CAR_KINDS), name="kind"),)


class WeatherSample(Base):
    """Track weather, sampled about once a minute (OpenF1 ``weather``)."""

    __tablename__ = "weather"

    session_key: Mapped[int] = mapped_column(_session_fk(), primary_key=True)
    date: Mapped[datetime] = mapped_column(UtcTime, primary_key=True)
    air_temperature: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    track_temperature: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    humidity: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    pressure: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    rainfall: Mapped[bool | None] = mapped_column(Boolean)
    wind_speed: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    wind_direction: Mapped[int | None] = mapped_column(Integer)


class SessionResult(Base):
    """Final classification of a session (OpenF1 ``session_result``)."""

    __tablename__ = "session_results"

    session_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    position: Mapped[int | None] = mapped_column(Integer)
    """Null when the driver is not classified."""
    points: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    number_of_laps: Mapped[int | None] = mapped_column(Integer)
    dnf: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    dns: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    dsq: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    duration_s: Mapped[Decimal | None] = mapped_column(LongSeconds)
    gap_to_leader_s: Mapped[Decimal | None] = mapped_column(LongSeconds)
    laps_down: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (_driver_fk(),)


class StartingGridSlot(Base):
    """A driver's grid slot, stored under the race session (OpenF1 ``starting_grid``).

    OpenF1 returns the grid under the qualifying session; the loader maps it to the race
    of the same meeting so every race table joins on one key.
    """

    __tablename__ = "starting_grid"

    session_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    position: Mapped[int] = mapped_column(Integer)
    quali_lap_duration: Mapped[Decimal | None] = mapped_column(Seconds)

    __table_args__ = (_driver_fk(),)


class IngestionRun(Base):
    """Audit row for every load attempt: what ran, how it went, what it wrote.

    No foreign key to ``sessions``: a run that fails before the session row exists is
    still recorded, and deleting a session keeps its history.
    """

    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    session_key: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(Text, server_default=text("'running'"))
    started_at: Mapped[datetime] = mapped_column(UtcTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(UtcTime)
    requests: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    rows_written: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    warnings: Mapped[list[str]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    error: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint(_one_of("status", RUN_STATUSES), name="status"),
        Index(None, "session_key", "started_at"),
    )
