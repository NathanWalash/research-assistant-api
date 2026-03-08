from collections.abc import Mapping
from dataclasses import dataclass
from itertools import islice
from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.parsing import (
    build_topic_id,
    iter_csv_rows,
    normalize_optional_text,
    parse_date,
    parse_int,
)
from research_assistant_api.models import Paper, Topic


@dataclass(slots=True)
class IngestionSummary:
    source_rows_processed: int = 0
    papers_upserted: int = 0
    topics_upserted: int = 0
    authors_upserted: int = 0
    institutions_upserted: int = 0
    authorships_upserted: int = 0
    citations_upserted: int = 0
    citation_import_skipped: bool = True


@dataclass(slots=True)
class ParsedDatasetRow:
    paper: dict[str, Any]
    topic: dict[str, Any] | None


def _build_upsert_statement(
    session: Session,
    table,
    rows: list[dict[str, Any]],
):
    dialect_name = session.bind.dialect.name if session.bind is not None else ""

    if dialect_name == "postgresql":
        return postgresql_insert(table).values(rows)
    if dialect_name == "sqlite":
        return sqlite_insert(table).values(rows)
    return None


def _upsert_rows(
    session: Session,
    table,
    rows: list[dict[str, Any]],
    *,
    conflict_columns: list[str],
    update_mapping: dict[str, Any] | None = None,
) -> None:
    if not rows:
        return

    statement = _build_upsert_statement(
        session,
        table,
        rows,
        conflict_columns=conflict_columns,
        update_mapping=update_mapping,
    )

    if statement is not None:
        if update_mapping:
            statement = statement.on_conflict_do_update(
                index_elements=conflict_columns,
                set_=update_mapping,
            )
        else:
            statement = statement.on_conflict_do_nothing(
                index_elements=conflict_columns,
            )
        session.execute(statement)
        return

    for row in rows:
        session.execute(table.insert().values(**row))


def parse_dataset_row(row: Mapping[str, str]) -> ParsedDatasetRow:
    paper_id = normalize_optional_text(row.get("id"))
    title = normalize_optional_text(row.get("display_name"))
    if paper_id is None or title is None:
        raise ValueError("CSV row is missing a paper id or title")

    topic_name = normalize_optional_text(row.get("primary_topic.display_name"))
    topic = None
    topic_id = None
    if topic_name is not None:
        topic_id = build_topic_id(topic_name)
        topic = {
            "id": topic_id,
            "name": topic_name,
            "field": None,
        }

    paper = {
        "id": paper_id,
        "title": title,
        "abstract": normalize_optional_text(row.get("abstract")),
        "publication_year": parse_int(row.get("publication_year")),
        "publication_date": parse_date(row.get("publication_date")),
        "citation_count": parse_int(row.get("cited_by_count")),
        "doi": normalize_optional_text(row.get("doi")),
        "journal": normalize_optional_text(row.get("primary_location.source.display_name")),
        "language": normalize_optional_text(row.get("language")),
        "work_type": normalize_optional_text(row.get("type")),
        "topic_id": topic_id,
    }

    return ParsedDatasetRow(paper=paper, topic=topic)


class CsvIngestionService:
    def __init__(self, session: Session):
        self.session = session

    def ingest(self, config: IngestionConfig) -> IngestionSummary:
        summary = IngestionSummary()
        topic_batch: dict[str, dict[str, Any]] = {}
        paper_batch: dict[str, dict[str, Any]] = {}

        rows = iter_csv_rows(config.csv_path)
        if config.limit is not None:
            rows = islice(rows, config.limit)

        for row in rows:
            parsed = parse_dataset_row(row)
            summary.source_rows_processed += 1

            if parsed.topic is not None:
                topic_batch[parsed.topic["id"]] = parsed.topic
            paper_batch[parsed.paper["id"]] = parsed.paper

            if summary.source_rows_processed % config.batch_size == 0:
                self._flush_topics_and_papers(topic_batch, paper_batch, summary)

        self._flush_topics_and_papers(topic_batch, paper_batch, summary)
        return summary

    def _flush_topics_and_papers(
        self,
        topic_batch: dict[str, dict[str, Any]],
        paper_batch: dict[str, dict[str, Any]],
        summary: IngestionSummary,
    ) -> None:
        if not topic_batch and not paper_batch:
            return

        topic_rows = list(topic_batch.values())
        paper_rows = list(paper_batch.values())

        if topic_rows:
            topic_table = Topic.__table__
            topic_insert = _build_upsert_statement(
                self.session,
                topic_table,
                topic_rows,
            )
            if topic_insert is not None:
                topic_insert = topic_insert.on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "name": topic_insert.excluded.name,
                        "field": func.coalesce(
                            topic_insert.excluded.field,
                            topic_table.c.field,
                        ),
                    },
                )
                self.session.execute(topic_insert)
            else:
                _upsert_rows(
                    self.session,
                    topic_table,
                    topic_rows,
                    conflict_columns=["id"],
                )

        if paper_rows:
            paper_table = Paper.__table__
            paper_insert = _build_upsert_statement(
                self.session,
                paper_table,
                paper_rows,
            )
            if paper_insert is not None:
                paper_insert = paper_insert.on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "title": paper_insert.excluded.title,
                        "abstract": func.coalesce(
                            paper_insert.excluded.abstract,
                            paper_table.c.abstract,
                        ),
                        "publication_year": paper_insert.excluded.publication_year,
                        "publication_date": func.coalesce(
                            paper_insert.excluded.publication_date,
                            paper_table.c.publication_date,
                        ),
                        "citation_count": paper_insert.excluded.citation_count,
                        "doi": func.coalesce(paper_insert.excluded.doi, paper_table.c.doi),
                        "journal": func.coalesce(
                            paper_insert.excluded.journal,
                            paper_table.c.journal,
                        ),
                        "language": func.coalesce(
                            paper_insert.excluded.language,
                            paper_table.c.language,
                        ),
                        "work_type": func.coalesce(
                            paper_insert.excluded.work_type,
                            paper_table.c.work_type,
                        ),
                        "topic_id": func.coalesce(
                            paper_insert.excluded.topic_id,
                            paper_table.c.topic_id,
                        ),
                    },
                )
                self.session.execute(paper_insert)
            else:
                _upsert_rows(
                    self.session,
                    paper_table,
                    paper_rows,
                    conflict_columns=["id"],
                )

        self.session.commit()
        summary.topics_upserted += len(topic_rows)
        summary.papers_upserted += len(paper_rows)
        topic_batch.clear()
        paper_batch.clear()
