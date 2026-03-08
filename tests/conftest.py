import pytest

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
def sqlite_database_url(tmp_path, monkeypatch: pytest.MonkeyPatch) -> str:
    database_path = tmp_path / "research_assistant_test.db"
    database_url = f"sqlite+pysqlite:///{database_path}"
    monkeypatch.setenv("RESEARCH_API_DATABASE_URL", database_url)
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")
    return database_url
