from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from research_assistant_api.db.session import (
    get_engine,
    get_session_factory,
    verify_database_connection,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
EXPECTED_TABLES = {
    "annotations",
    "authors",
    "citations",
    "institutions",
    "paper_authors",
    "papers",
    "projects",
    "reading_list_items",
    "topics",
    "users",
}


def test_database_session_executes_simple_query(sqlite_database_url: str) -> None:
    verify_database_connection(sqlite_database_url)

    session_factory = get_session_factory(sqlite_database_url)
    with session_factory() as session:
        result = session.execute(text("SELECT 1")).scalar_one()

    assert result == 1


def test_alembic_upgrade_creates_initial_schema(sqlite_database_url: str) -> None:
    config = Config(str(ROOT_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT_DIR / "alembic"))

    command.upgrade(config, "head")

    inspector = inspect(get_engine(sqlite_database_url))
    assert EXPECTED_TABLES.issubset(set(inspector.get_table_names()))
