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
    parse_bool,
    parse_date,
    parse_int,
    split_pipe_values,
)
from research_assistant_api.models import Author, Institution, Paper, PaperAuthor, Topic


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
    authors: list[dict[str, Any]]
    institutions: list[dict[str, Any]]
    authorships: list[dict[str, Any]]


def _merge_prefer_non_null(
    existing: dict[str, Any] | None,
    incoming: dict[str, Any],
) -> dict[str, Any]:
    if existing is None:
        return incoming

    merged = existing.copy()
    for key, value in incoming.items():
        if value is not None:
            merged[key] = value
    return merged


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

    institution_names = split_pipe_values(row.get("authorships.institutions.display_name"))
    institution_ids = split_pipe_values(row.get("authorships.institutions.id"))
    countries = split_pipe_values(row.get("authorships.countries"))
    unique_country = None
    if countries:
        distinct_countries = sorted(set(countries))
        if len(distinct_countries) == 1:
            unique_country = distinct_countries[0]

    institutions_by_id: dict[str, dict[str, Any]] = {}
    for institution_id, institution_name in zip(institution_ids, institution_names, strict=False):
        if not institution_id or not institution_name:
            continue
        institutions_by_id[institution_id] = {
            "id": institution_id,
            "name": institution_name,
            "country": unique_country if len(institution_ids) == 1 else None,
        }

    resolved_author_institution_id = None
    if len(institutions_by_id) == 1:
        resolved_author_institution_id = next(iter(institutions_by_id))

    author_names = split_pipe_values(row.get("authorships.author.display_name"))
    author_ids = split_pipe_values(row.get("authorships.author.id"))
    author_orcids = split_pipe_values(row.get("authorships.author.orcid"))
    corresponding_flags = split_pipe_values(row.get("authorships.is_corresponding"))

    authors: list[dict[str, Any]] = []
    authorships: list[dict[str, Any]] = []
    seen_author_ids: set[str] = set()

    author_count = max(
        len(author_names),
        len(author_ids),
        len(author_orcids),
        len(corresponding_flags),
    )

    for index in range(author_count):
        author_id = author_ids[index] if index < len(author_ids) else None
        author_name = author_names[index] if index < len(author_names) else None
        author_orcid = author_orcids[index] if index < len(author_orcids) else None
        is_corresponding = (
            corresponding_flags[index] if index < len(corresponding_flags) else None
        )

        if not author_id or not author_name:
            continue

        if author_id not in seen_author_ids:
            authors.append(
                {
                    "id": author_id,
                    "name": author_name,
                    "orcid": author_orcid or None,
                    "institution_id": resolved_author_institution_id,
                }
            )
            seen_author_ids.add(author_id)

        authorships.append(
            {
                "paper_id": paper_id,
                "author_id": author_id,
                "author_position": index + 1,
                "is_corresponding": parse_bool(is_corresponding),
            }
        )

    return ParsedDatasetRow(
        paper=paper,
        topic=topic,
        authors=authors,
        institutions=list(institutions_by_id.values()),
        authorships=authorships,
    )


class CsvIngestionService:
    def __init__(self, session: Session):
        self.session = session

    def ingest(self, config: IngestionConfig) -> IngestionSummary:
        summary = IngestionSummary()
        topic_batch: dict[str, dict[str, Any]] = {}
        paper_batch: dict[str, dict[str, Any]] = {}
        author_batch: dict[str, dict[str, Any]] = {}
        institution_batch: dict[str, dict[str, Any]] = {}
        authorship_batch: dict[tuple[str, str], dict[str, Any]] = {}

        rows = iter_csv_rows(config.csv_path)
        if config.limit is not None:
            rows = islice(rows, config.limit)

        for row in rows:
            parsed = parse_dataset_row(row)
            summary.source_rows_processed += 1

            if parsed.topic is not None:
                topic_batch[parsed.topic["id"]] = _merge_prefer_non_null(
                    topic_batch.get(parsed.topic["id"]),
                    parsed.topic,
                )
            paper_batch[parsed.paper["id"]] = _merge_prefer_non_null(
                paper_batch.get(parsed.paper["id"]),
                parsed.paper,
            )
            for institution in parsed.institutions:
                institution_batch[institution["id"]] = _merge_prefer_non_null(
                    institution_batch.get(institution["id"]),
                    institution,
                )
            for author in parsed.authors:
                author_batch[author["id"]] = _merge_prefer_non_null(
                    author_batch.get(author["id"]),
                    author,
                )
            for authorship in parsed.authorships:
                authorship_batch[(authorship["paper_id"], authorship["author_id"])] = authorship

            if summary.source_rows_processed % config.batch_size == 0:
                self._flush_batch(
                    topic_batch,
                    paper_batch,
                    author_batch,
                    institution_batch,
                    authorship_batch,
                    summary,
                )

        self._flush_batch(
            topic_batch,
            paper_batch,
            author_batch,
            institution_batch,
            authorship_batch,
            summary,
        )
        return summary

    def _flush_batch(
        self,
        topic_batch: dict[str, dict[str, Any]],
        paper_batch: dict[str, dict[str, Any]],
        author_batch: dict[str, dict[str, Any]],
        institution_batch: dict[str, dict[str, Any]],
        authorship_batch: dict[tuple[str, str], dict[str, Any]],
        summary: IngestionSummary,
    ) -> None:
        if (
            not topic_batch
            and not paper_batch
            and not author_batch
            and not institution_batch
            and not authorship_batch
        ):
            return

        topic_rows = list(topic_batch.values())
        paper_rows = list(paper_batch.values())
        institution_rows = list(institution_batch.values())
        author_rows = list(author_batch.values())
        authorship_rows = list(authorship_batch.values())

        if institution_rows:
            institution_table = Institution.__table__
            institution_insert = _build_upsert_statement(
                self.session,
                institution_table,
                institution_rows,
            )
            if institution_insert is not None:
                institution_insert = institution_insert.on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "name": institution_insert.excluded.name,
                        "country": func.coalesce(
                            institution_insert.excluded.country,
                            institution_table.c.country,
                        ),
                    },
                )
                self.session.execute(institution_insert)
            else:
                _upsert_rows(
                    self.session,
                    institution_table,
                    institution_rows,
                    conflict_columns=["id"],
                )

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

        if author_rows:
            author_table = Author.__table__
            author_insert = _build_upsert_statement(
                self.session,
                author_table,
                author_rows,
            )
            if author_insert is not None:
                author_insert = author_insert.on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "name": author_insert.excluded.name,
                        "orcid": func.coalesce(
                            author_insert.excluded.orcid,
                            author_table.c.orcid,
                        ),
                        "institution_id": func.coalesce(
                            author_insert.excluded.institution_id,
                            author_table.c.institution_id,
                        ),
                    },
                )
                self.session.execute(author_insert)
            else:
                _upsert_rows(
                    self.session,
                    author_table,
                    author_rows,
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

        if authorship_rows:
            _upsert_rows(
                self.session,
                PaperAuthor.__table__,
                authorship_rows,
                conflict_columns=["paper_id", "author_id"],
            )

        self.session.commit()
        summary.institutions_upserted += len(institution_rows)
        summary.topics_upserted += len(topic_rows)
        summary.authors_upserted += len(author_rows)
        summary.papers_upserted += len(paper_rows)
        summary.authorships_upserted += len(authorship_rows)
        institution_batch.clear()
        topic_batch.clear()
        author_batch.clear()
        paper_batch.clear()
        authorship_batch.clear()
