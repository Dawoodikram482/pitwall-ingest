"""Service settings, read from environment variables and an optional `.env` file."""

from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "postgresql+psycopg://pitwall:pitwall@localhost:5432/pitwall"


class Settings(BaseSettings):
    """Configuration for the ingest service.

    Every field can be set with an environment variable of the same name in capitals,
    e.g. ``DATABASE_URL``.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: PostgresDsn = PostgresDsn(DEFAULT_DATABASE_URL)
    """SQLAlchemy URL of the Postgres database (driver: psycopg 3)."""


@lru_cache
def get_settings() -> Settings:
    """Return the settings, loaded once per process."""
    return Settings()
