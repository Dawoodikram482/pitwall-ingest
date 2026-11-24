"""Settings and engine creation."""

import pytest

from pitwall_ingest.adapters.db import create_db_engine
from pitwall_ingest.config import DEFAULT_DATABASE_URL, Settings, get_settings


def test_database_url_defaults_to_local_compose_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings(_env_file=None)

    assert str(settings.database_url) == DEFAULT_DATABASE_URL


def test_database_url_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@db.example.com:6543/f1")

    settings = Settings(_env_file=None)

    assert settings.database_url.hosts()[0]["host"] == "db.example.com"
    assert settings.database_url.path == "/f1"


def test_non_postgres_url_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "mysql://u:p@localhost/f1")

    with pytest.raises(ValueError, match="URL scheme"):
        Settings(_env_file=None)


def test_engine_uses_the_given_url_or_the_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@settings-host:5432/f1")
    get_settings.cache_clear()
    try:
        assert create_db_engine().url.host == "settings-host"
        assert create_db_engine("postgresql+psycopg://u:p@other:5432/f1").url.host == "other"
    finally:
        get_settings.cache_clear()
