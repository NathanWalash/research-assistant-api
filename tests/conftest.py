from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from research_assistant_api.core.config import get_settings
from research_assistant_api.db.session import reset_database_state


@pytest.fixture(autouse=True)
def reset_app_state() -> None:
    get_settings.cache_clear()
    reset_database_state()
    yield
    get_settings.cache_clear()
    reset_database_state()


@pytest.fixture
def sqlite_database_url(monkeypatch: pytest.MonkeyPatch) -> str:
    database_name = f"research_assistant_test_{uuid4().hex}"
    database_url = (
        f"sqlite+pysqlite:///file:{database_name}?mode=memory&cache=shared&uri=true"
    )
    keepalive_engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False, "uri": True},
    )
    keepalive_connection = keepalive_engine.connect()
    monkeypatch.setenv("RESEARCH_API_DATABASE_URL", database_url)
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")
    try:
        yield database_url
    finally:
        keepalive_connection.close()
        keepalive_engine.dispose()
