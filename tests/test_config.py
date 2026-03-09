import pytest
from pydantic import ValidationError

from research_assistant_api.core.config import (
    DEFAULT_JWT_SECRET_KEY,
    MIN_JWT_SECRET_KEY_LENGTH,
    Settings,
    normalize_database_url,
)


def test_settings_allow_development_default_secret() -> None:
    settings = Settings(
        environment="development",
        jwt_secret_key=DEFAULT_JWT_SECRET_KEY,
    )

    assert settings.jwt_secret_key == DEFAULT_JWT_SECRET_KEY


def test_settings_reject_production_default_secret() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            environment="production",
            jwt_secret_key=DEFAULT_JWT_SECRET_KEY,
        )

    assert "must not use the development default" in str(exc_info.value)


def test_settings_reject_short_production_secret() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            environment="production",
            jwt_secret_key="short-secret",
        )

    assert f"at least {MIN_JWT_SECRET_KEY_LENGTH} characters" in str(exc_info.value)


def test_settings_allow_long_production_secret() -> None:
    settings = Settings(
        environment="production",
        jwt_secret_key="x" * MIN_JWT_SECRET_KEY_LENGTH,
    )

    assert settings.environment == "production"


def test_normalize_database_url_handles_railway_postgres_aliases() -> None:
    assert (
        normalize_database_url("postgres://user:pass@host:5432/db")
        == "postgresql+psycopg://user:pass@host:5432/db"
    )
    assert (
        normalize_database_url("postgresql://user:pass@host:5432/db?sslmode=require")
        == "postgresql+psycopg://user:pass@host:5432/db?sslmode=require"
    )
    assert (
        normalize_database_url("sqlite+pysqlite:///file:test.db")
        == "sqlite+pysqlite:///file:test.db"
    )


def test_settings_normalize_database_url() -> None:
    settings = Settings(
        environment="development",
        database_url="postgres://user:pass@host:5432/db",
    )

    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/db"
