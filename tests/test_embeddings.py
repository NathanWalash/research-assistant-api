from pathlib import Path

from sqlalchemy import select

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine, get_session_factory
from research_assistant_api.embeddings import (
    PaperEmbeddingService,
    build_embedding_text,
)
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService
from research_assistant_api.models import Paper
from research_assistant_api.repositories.embedding_repository import EmbeddingRepository

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeEmbedder:
    def encode_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(index + 1), 0.0, 0.0] for index, _ in enumerate(texts)]


def test_build_embedding_text_uses_title_and_abstract() -> None:
    paper = Paper(
        id="paper-1",
        title="Paper One",
        abstract="Sample abstract",
        publication_year=2024,
        citation_count=0,
    )

    assert build_embedding_text(paper) == "Paper One\n\nSample abstract"


def test_embedding_pipeline_stores_generated_embeddings(
    sqlite_database_url: str,
) -> None:
    engine = get_engine(sqlite_database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(sqlite_database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_openalex_leeds.csv",
        citation_csv_path=None,
        batch_size=10,
    )

    with session_factory() as session:
        CsvIngestionService(session).ingest(config)
        service = PaperEmbeddingService(
            repository=EmbeddingRepository(session),
            embedder=FakeEmbedder(),
        )
        summary = service.generate_embeddings(limit=None, paper_id=None, force=False)
        papers = session.scalars(select(Paper).order_by(Paper.id.asc())).all()

    assert summary.papers_selected == 2
    assert summary.papers_embedded == 2
    assert papers[0].embedding == [1.0, 0.0, 0.0]
    assert papers[1].embedding == [2.0, 0.0, 0.0]
