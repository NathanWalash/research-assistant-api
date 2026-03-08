from pathlib import Path

from sqlalchemy import func
from sqlalchemy import select

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine, get_session_factory
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService
from research_assistant_api.models import Paper, Topic

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_csv_ingestion_imports_topics_and_papers(sqlite_database_url: str) -> None:
    engine = get_engine(sqlite_database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(sqlite_database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_openalex_leeds.csv",
        citation_csv_path=None,
        batch_size=1,
    )

    with session_factory() as session:
        summary = CsvIngestionService(session).ingest(config)
        papers = session.scalars(select(Paper).order_by(Paper.publication_year.desc())).all()
        topics = session.scalars(select(Topic).order_by(Topic.name)).all()

    assert summary.source_rows_processed == 2
    assert summary.papers_upserted == 2
    assert summary.topics_upserted == 2

    assert [topic.id for topic in topics] == [
        "topic:artificial-intelligence",
        "topic:computer-vision",
    ]
    assert [paper.id for paper in papers] == [
        "https://openalex.org/W1",
        "https://openalex.org/W2",
    ]
    assert papers[0].topic_id == "topic:computer-vision"
    assert papers[0].citation_count == 12
    assert papers[0].journal == "Journal One"
    assert papers[1].abstract is None


def test_csv_ingestion_is_idempotent_for_papers_and_topics(
    sqlite_database_url: str,
) -> None:
    engine = get_engine(sqlite_database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(sqlite_database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_openalex_leeds.csv",
        citation_csv_path=None,
        batch_size=50,
    )

    with session_factory() as session:
        service = CsvIngestionService(session)
        service.ingest(config)
        service.ingest(config)

        paper_count = session.scalar(select(func.count()).select_from(Paper))
        topic_count = session.scalar(select(func.count()).select_from(Topic))

    assert paper_count == 2
    assert topic_count == 2
