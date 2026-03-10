from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy.orm import Session

from research_assistant_api.repositories.analytics_repository import AnalyticsRepository
from research_assistant_api.repositories.author_repository import AuthorRepository
from research_assistant_api.repositories.citation_repository import CitationRepository
from research_assistant_api.repositories.paper_repository import PaperRepository
from research_assistant_api.repositories.similarity_repository import SimilarityRepository
from research_assistant_api.repositories.topic_repository import TopicRepository
from research_assistant_api.services import (
    AnalyticsService,
    AuthorService,
    CitationGraphService,
    CitationPathNotFoundError,
    DiscoveryNotFoundError,
    PaperEmbeddingNotAvailableError,
    PaperService,
    SimilarityService,
    TopicService,
)


def _validate_limit_offset(limit: int, offset: int) -> None:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0")


def _model_to_json(value: Any) -> Any:
    if isinstance(value, list):
        return [_model_to_json(item) for item in value]
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def register_public_tools(
    mcp: FastMCP,
    *,
    session_factory: Callable[[], Session],
) -> None:
    @mcp.tool(
        name="papers_search",
        description="Search papers by query, topic, year, and minimum citation count.",
    )
    def papers_search(
        query: str | None = None,
        topic: str | None = None,
        year: int | None = None,
        citation_count: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        _validate_limit_offset(limit, offset)
        if year is not None and year < 0:
            raise ValueError("year must be greater than or equal to 0")
        if citation_count is not None and citation_count < 0:
            raise ValueError("citation_count must be greater than or equal to 0")
        with session_factory() as session:
            service = PaperService(PaperRepository(session))
            return _model_to_json(
                service.search_papers(
                    query=query,
                    topic=topic,
                    year=year,
                    citation_count=citation_count,
                    limit=limit,
                    offset=offset,
                )
            )

    @mcp.tool(
        name="papers_get",
        description="Get a paper with metadata, authorship, and topic details.",
    )
    def papers_get(paper_id: str) -> dict[str, Any]:
        with session_factory() as session:
            service = PaperService(PaperRepository(session))
            try:
                return _model_to_json(service.get_paper(paper_id))
            except DiscoveryNotFoundError as error:
                raise ValueError(str(error)) from error

    @mcp.tool(
        name="papers_similar",
        description="List semantically similar papers using stored embeddings.",
    )
    def papers_similar(
        paper_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        _validate_limit_offset(limit, offset)
        with session_factory() as session:
            service = SimilarityService(SimilarityRepository(session))
            try:
                return _model_to_json(
                    service.list_similar_papers(
                        paper_id,
                        limit=limit,
                        offset=offset,
                    )
                )
            except (DiscoveryNotFoundError, PaperEmbeddingNotAvailableError) as error:
                raise ValueError(str(error)) from error

    @mcp.tool(
        name="papers_citations",
        description="Get citation neighbourhood within the Leeds citation subgraph.",
    )
    def papers_citations(
        paper_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        _validate_limit_offset(limit, offset)
        with session_factory() as session:
            service = CitationGraphService(
                citation_repository=CitationRepository(session),
                paper_repository=PaperRepository(session),
            )
            try:
                return _model_to_json(
                    service.get_citation_neighborhood(
                        paper_id,
                        limit=limit,
                        offset=offset,
                    )
                )
            except DiscoveryNotFoundError as error:
                raise ValueError(str(error)) from error

    @mcp.tool(
        name="papers_path",
        description="Find a directed shortest citation path in the Leeds subgraph.",
    )
    def papers_path(
        paper_id: str,
        target_paper_id: str,
        max_depth: int = 6,
    ) -> dict[str, Any]:
        if max_depth < 1 or max_depth > 12:
            raise ValueError("max_depth must be between 1 and 12")
        with session_factory() as session:
            service = CitationGraphService(
                citation_repository=CitationRepository(session),
                paper_repository=PaperRepository(session),
            )
            try:
                return _model_to_json(
                    service.get_citation_path(
                        paper_id,
                        target_paper_id,
                        max_depth=max_depth,
                    )
                )
            except (DiscoveryNotFoundError, CitationPathNotFoundError) as error:
                raise ValueError(str(error)) from error

    @mcp.tool(
        name="authors_list",
        description="List authors in the Leeds subset.",
    )
    def authors_list(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        _validate_limit_offset(limit, offset)
        with session_factory() as session:
            service = AuthorService(AuthorRepository(session))
            return _model_to_json(
                service.list_authors(query=None, limit=limit, offset=offset)
            )

    @mcp.tool(
        name="authors_search",
        description="Search authors by name or author id.",
    )
    def authors_search(
        query: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        _validate_limit_offset(limit, offset)
        if not query.strip():
            raise ValueError("query must be a non-empty string")
        with session_factory() as session:
            service = AuthorService(AuthorRepository(session))
            return _model_to_json(
                service.list_authors(query=query, limit=limit, offset=offset)
            )

    @mcp.tool(
        name="authors_get",
        description="Get author metadata and affiliation details.",
    )
    def authors_get(author_id: str) -> dict[str, Any]:
        with session_factory() as session:
            service = AuthorService(AuthorRepository(session))
            try:
                return _model_to_json(service.get_author(author_id))
            except DiscoveryNotFoundError as error:
                raise ValueError(str(error)) from error

    @mcp.tool(
        name="authors_papers",
        description="List papers for a specific author id.",
    )
    def authors_papers(
        author_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        _validate_limit_offset(limit, offset)
        with session_factory() as session:
            service = AuthorService(AuthorRepository(session))
            try:
                return _model_to_json(
                    service.list_author_papers(author_id, limit=limit, offset=offset)
                )
            except DiscoveryNotFoundError as error:
                raise ValueError(str(error)) from error

    @mcp.tool(
        name="topics_list",
        description="List topics in the Leeds subset.",
    )
    def topics_list(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        _validate_limit_offset(limit, offset)
        with session_factory() as session:
            service = TopicService(TopicRepository(session))
            return _model_to_json(service.list_topics(limit=limit, offset=offset))

    @mcp.tool(
        name="topics_papers",
        description="List papers assigned to a topic id.",
    )
    def topics_papers(
        topic_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        _validate_limit_offset(limit, offset)
        with session_factory() as session:
            service = TopicService(TopicRepository(session))
            try:
                return _model_to_json(
                    service.list_topic_papers(topic_id, limit=limit, offset=offset)
                )
            except DiscoveryNotFoundError as error:
                raise ValueError(str(error)) from error

    @mcp.tool(
        name="analytics_top_papers",
        description="Rank papers by citation count with optional topic/year filters.",
    )
    def analytics_top_papers(
        topic: str | None = None,
        year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        _validate_limit_offset(limit, offset)
        if year is not None and year < 0:
            raise ValueError("year must be greater than or equal to 0")
        with session_factory() as session:
            service = AnalyticsService(AnalyticsRepository(session))
            return _model_to_json(
                service.list_top_papers(
                    topic=topic,
                    year=year,
                    limit=limit,
                    offset=offset,
                )
            )

    @mcp.tool(
        name="analytics_topics",
        description="Summarise topic coverage and citation totals.",
    )
    def analytics_topics(
        year: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        _validate_limit_offset(limit, offset)
        if year is not None and year < 0:
            raise ValueError("year must be greater than or equal to 0")
        with session_factory() as session:
            service = AnalyticsService(AnalyticsRepository(session))
            return _model_to_json(
                service.list_topic_distribution(year=year, limit=limit, offset=offset)
            )

    @mcp.tool(
        name="analytics_trends",
        description="Summarise publication output and citation totals by year.",
    )
    def analytics_trends(
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[dict[str, Any]]:
        if start_year is not None and start_year < 0:
            raise ValueError("start_year must be greater than or equal to 0")
        if end_year is not None and end_year < 0:
            raise ValueError("end_year must be greater than or equal to 0")
        with session_factory() as session:
            service = AnalyticsService(AnalyticsRepository(session))
            return _model_to_json(
                service.list_publication_trends(
                    start_year=start_year,
                    end_year=end_year,
                )
            )
