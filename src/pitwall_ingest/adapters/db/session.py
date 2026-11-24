"""Database engine creation."""

from sqlalchemy import Engine, create_engine

from pitwall_ingest.config import get_settings


def create_db_engine(url: str | None = None, *, echo: bool = False) -> Engine:
    """Create an engine for ``url``, or for ``DATABASE_URL`` from the settings.

    ``pool_pre_ping`` makes the pool drop connections the server closed, which free
    hosted Postgres tiers do when they scale to zero.
    """
    return create_engine(url or str(get_settings().database_url), echo=echo, pool_pre_ping=True)
