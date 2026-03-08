from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from research_assistant_api.core.config import get_settings


def _connect_args(database_url: str) -> dict[str, bool]:
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if "uri=true" in database_url:
            connect_args["uri"] = True
        return connect_args
    return {}


@lru_cache
def get_engine(database_url: str | None = None) -> Engine:
    resolved_url = database_url or get_settings().database_url
    return create_engine(
        resolved_url,
        future=True,
        pool_pre_ping=True,
        connect_args=_connect_args(resolved_url),
    )


@lru_cache
def get_session_factory(
    database_url: str | None = None,
) -> sessionmaker[Session]:
    resolved_url = database_url or get_settings().database_url
    return sessionmaker(
        bind=get_engine(resolved_url),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_db() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    with session_factory() as session:
        yield session


def verify_database_connection(database_url: str | None = None) -> None:
    with get_engine(database_url).connect() as connection:
        connection.execute(text("SELECT 1"))


def reset_database_state() -> None:
    get_engine.cache_clear()
    get_session_factory.cache_clear()
