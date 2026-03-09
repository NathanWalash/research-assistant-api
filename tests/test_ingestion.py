from pathlib import Path

from sqlalchemy import func
from sqlalchemy import select

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine, get_session_factory
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService
from research_assistant_api.models import (
    Author,
    Citation,
    Institution,
    Paper,
    PaperAuthor,
    Topic,
)

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
        papers = session.scalars(
            select(Paper).order_by(Paper.publication_year.desc())
        ).all()
        topics = session.scalars(select(Topic).order_by(Topic.name)).all()

    assert summary.source_rows_processed == 2
    assert summary.papers_upserted == 2
    assert summary.topics_upserted == 2
    assert summary.citation_import_skipped is True

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


def test_csv_ingestion_imports_authors_institutions_and_authorships(
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
        summary = CsvIngestionService(session).ingest(config)
        authors = session.scalars(select(Author).order_by(Author.name)).all()
        institutions = session.scalars(
            select(Institution).order_by(Institution.name)
        ).all()
        authorships = session.scalars(
            select(PaperAuthor).order_by(
                PaperAuthor.paper_id, PaperAuthor.author_position
            )
        ).all()

    assert summary.authors_upserted == 3
    assert summary.institutions_upserted == 2
    assert summary.authorships_upserted == 4

    assert [author.id for author in authors] == [
        "https://openalex.org/A1",
        "https://openalex.org/A2",
        "https://openalex.org/A3",
    ]
    assert authors[0].institution_id == "https://openalex.org/I1"
    assert authors[2].institution_id is None

    assert [institution.id for institution in institutions] == [
        "https://openalex.org/I2",
        "https://openalex.org/I1",
    ]
    assert institutions[1].country == "GB"
    assert institutions[0].country is None

    assert [(item.paper_id, item.author_id) for item in authorships] == [
        ("https://openalex.org/W1", "https://openalex.org/A1"),
        ("https://openalex.org/W1", "https://openalex.org/A2"),
        ("https://openalex.org/W2", "https://openalex.org/A1"),
        ("https://openalex.org/W2", "https://openalex.org/A3"),
    ]
    assert authorships[0].is_corresponding is True
    assert authorships[-1].author_position == 2


def test_csv_ingestion_imports_optional_citation_edges(
    sqlite_database_url: str,
) -> None:
    engine = get_engine(sqlite_database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(sqlite_database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_openalex_leeds.csv",
        citation_csv_path=FIXTURES_DIR / "sample_citation_edges.csv",
        batch_size=10,
    )

    with session_factory() as session:
        summary = CsvIngestionService(session).ingest(config)
        citations = session.scalars(select(Citation)).all()

    assert summary.citation_import_skipped is False
    assert summary.citations_upserted == 1
    assert [
        (citation.citing_paper_id, citation.cited_paper_id) for citation in citations
    ] == [("https://openalex.org/W2", "https://openalex.org/W1")]


def test_csv_ingestion_preserves_richer_duplicate_metadata(
    sqlite_database_url: str,
) -> None:
    engine = get_engine(sqlite_database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(sqlite_database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_duplicate_metadata_rows.csv",
        citation_csv_path=None,
        batch_size=50,
    )

    with session_factory() as session:
        summary = CsvIngestionService(session).ingest(config)
        paper = session.scalar(
            select(Paper).where(Paper.id == "https://openalex.org/W9")
        )
        author = session.scalar(
            select(Author).where(Author.id == "https://openalex.org/A9")
        )
        topic = session.scalar(select(Topic).where(Topic.id == "topic:data-science"))

        paper_count = session.scalar(select(func.count()).select_from(Paper))
        author_count = session.scalar(select(func.count()).select_from(Author))
        topic_count = session.scalar(select(func.count()).select_from(Topic))

    assert summary.source_rows_processed == 2
    assert summary.papers_upserted == 1
    assert summary.authors_upserted == 1
    assert paper_count == 1
    assert author_count == 1
    assert topic_count == 1
    assert paper is not None
    assert author is not None
    assert topic is not None
    assert paper.abstract == "Rich abstract"
    assert paper.doi == "https://doi.org/10.1234/dup"
    assert paper.topic_id == "topic:data-science"
    assert author.orcid == "https://orcid.org/0000-0000-0000-0009"


def test_csv_ingestion_skips_invalid_citation_edge_rows(
    sqlite_database_url: str,
) -> None:
    engine = get_engine(sqlite_database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(sqlite_database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_openalex_leeds.csv",
        citation_csv_path=FIXTURES_DIR / "sample_citation_edges_invalid.csv",
        batch_size=10,
    )

    with session_factory() as session:
        summary = CsvIngestionService(session).ingest(config)
        citation_count = session.scalar(select(func.count()).select_from(Citation))

    assert summary.citation_import_skipped is False
    assert summary.citations_upserted == 1
    assert citation_count == 1


def test_csv_ingestion_skips_rows_missing_required_paper_fields(
    sqlite_database_url: str,
) -> None:
    engine = get_engine(sqlite_database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(sqlite_database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_openalex_leeds_invalid_row.csv",
        citation_csv_path=None,
        batch_size=10,
    )

    with session_factory() as session:
        summary = CsvIngestionService(session).ingest(config)
        paper_count = session.scalar(select(func.count()).select_from(Paper))

    assert summary.source_rows_processed == 2
    assert summary.source_rows_skipped == 1
    assert summary.papers_upserted == 2
    assert paper_count == 2


def test_csv_ingestion_allows_duplicate_orcids_across_author_ids(
    sqlite_database_url: str,
) -> None:
    engine = get_engine(sqlite_database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(sqlite_database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_duplicate_author_orcid.csv",
        citation_csv_path=None,
        batch_size=10,
    )

    with session_factory() as session:
        summary = CsvIngestionService(session).ingest(config)
        authors = session.scalars(select(Author).order_by(Author.id.asc())).all()

    assert summary.source_rows_processed == 2
    assert summary.source_rows_skipped == 0
    assert summary.authors_upserted == 2
    assert [author.id for author in authors] == [
        "https://openalex.org/A10",
        "https://openalex.org/A11",
    ]
    assert authors[0].orcid == "https://orcid.org/0000-0000-0000-0010"
    assert authors[1].orcid == "https://orcid.org/0000-0000-0000-0010"


def test_csv_ingestion_accepts_titles_longer_than_previous_varchar_limit(
    sqlite_database_url: str,
) -> None:
    engine = get_engine(sqlite_database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(sqlite_database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_long_title.csv",
        citation_csv_path=None,
        batch_size=10,
    )

    with session_factory() as session:
        summary = CsvIngestionService(session).ingest(config)
        paper = session.scalar(select(Paper).where(Paper.id == "https://openalex.org/W-long"))

    assert summary.source_rows_processed == 1
    assert summary.source_rows_skipped == 0
    assert summary.papers_upserted == 1
    assert paper is not None
    assert len(paper.title) > 512


def test_csv_ingestion_allows_duplicate_dois_across_paper_ids(
    sqlite_database_url: str,
) -> None:
    engine = get_engine(sqlite_database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(sqlite_database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_duplicate_paper_doi.csv",
        citation_csv_path=None,
        batch_size=10,
    )

    with session_factory() as session:
        summary = CsvIngestionService(session).ingest(config)
        papers = session.scalars(select(Paper).order_by(Paper.id.asc())).all()

    assert summary.source_rows_processed == 2
    assert summary.source_rows_skipped == 0
    assert summary.papers_upserted == 2
    assert [paper.id for paper in papers] == [
        "https://openalex.org/W20",
        "https://openalex.org/W21",
    ]
    assert papers[0].doi == "https://doi.org/10.1234/shared"
    assert papers[1].doi == "https://doi.org/10.1234/shared"
