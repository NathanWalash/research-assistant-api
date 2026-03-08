from research_assistant_api.models import Paper, PaperAuthor
from research_assistant_api.repositories.author_repository import AuthorRecord, AuthorRepository
from research_assistant_api.repositories.paper_repository import PaperRepository
from research_assistant_api.repositories.topic_repository import TopicRecord, TopicRepository
from research_assistant_api.schemas.discovery import (
    AuthorDetail,
    InstitutionSummary,
    PaperAuthorSummary,
    PaperDetail,
    PaperSummary,
    TopicListItem,
    TopicSummary,
)


class DiscoveryNotFoundError(Exception):
    def __init__(self, resource_name: str, resource_id: str):
        self.resource_name = resource_name
        self.resource_id = resource_id
        super().__init__(f"{resource_name} '{resource_id}' was not found")


def _build_topic_summary(topic: object | None) -> TopicSummary | None:
    if topic is None:
        return None
    return TopicSummary.model_validate(topic)


def _build_institution_summary(institution: object | None) -> InstitutionSummary | None:
    if institution is None:
        return None
    return InstitutionSummary.model_validate(institution)


def _build_paper_summary(paper: Paper) -> PaperSummary:
    return PaperSummary(
        id=paper.id,
        title=paper.title,
        publication_year=paper.publication_year,
        publication_date=paper.publication_date,
        citation_count=paper.citation_count,
        doi=paper.doi,
        journal=paper.journal,
        language=paper.language,
        work_type=paper.work_type,
        topic=_build_topic_summary(paper.topic),
    )


def _author_sort_key(authorship: PaperAuthor) -> tuple[int, str]:
    if authorship.author_position is None:
        return (10**9, authorship.author.name.lower())
    return (authorship.author_position, authorship.author.name.lower())


def _build_paper_detail(paper: Paper) -> PaperDetail:
    authors = [
        PaperAuthorSummary(
            id=authorship.author.id,
            name=authorship.author.name,
            orcid=authorship.author.orcid,
            institution=_build_institution_summary(authorship.author.institution),
            author_position=authorship.author_position,
            is_corresponding=authorship.is_corresponding,
        )
        for authorship in sorted(paper.authorships, key=_author_sort_key)
    ]

    summary = _build_paper_summary(paper)
    return PaperDetail(
        **summary.model_dump(),
        abstract=paper.abstract,
        authors=authors,
    )


def _build_author_detail(record: AuthorRecord) -> AuthorDetail:
    return AuthorDetail(
        id=record.author.id,
        name=record.author.name,
        orcid=record.author.orcid,
        institution=_build_institution_summary(record.author.institution),
        paper_count=record.paper_count,
    )


def _build_topic_list_item(record: TopicRecord) -> TopicListItem:
    return TopicListItem(
        id=record.topic.id,
        name=record.topic.name,
        field=record.topic.field,
        paper_count=record.paper_count,
    )


class PaperService:
    def __init__(self, repository: PaperRepository):
        self.repository = repository

    def get_paper(self, paper_id: str) -> PaperDetail:
        paper = self.repository.get_by_id(paper_id)
        if paper is None:
            raise DiscoveryNotFoundError("paper", paper_id)
        return _build_paper_detail(paper)

    def search_papers(
        self,
        *,
        query: str | None,
        topic: str | None,
        year: int | None,
        citation_count: int | None,
        limit: int,
        offset: int,
    ) -> list[PaperSummary]:
        papers = self.repository.search(
            query=query,
            topic=topic,
            year=year,
            citation_count=citation_count,
            limit=limit,
            offset=offset,
        )
        return [_build_paper_summary(paper) for paper in papers]


class AuthorService:
    def __init__(self, repository: AuthorRepository):
        self.repository = repository

    def get_author(self, author_id: str) -> AuthorDetail:
        author_record = self.repository.get_by_id(author_id)
        if author_record is None:
            raise DiscoveryNotFoundError("author", author_id)
        return _build_author_detail(author_record)

    def list_author_papers(self, author_id: str, *, limit: int, offset: int) -> list[PaperSummary]:
        if self.repository.get_by_id(author_id) is None:
            raise DiscoveryNotFoundError("author", author_id)
        papers = self.repository.list_papers(author_id, limit=limit, offset=offset)
        return [_build_paper_summary(paper) for paper in papers]


class TopicService:
    def __init__(self, repository: TopicRepository):
        self.repository = repository

    def list_topics(self, *, limit: int, offset: int) -> list[TopicListItem]:
        topic_records = self.repository.list_topics(limit=limit, offset=offset)
        return [_build_topic_list_item(record) for record in topic_records]

    def list_topic_papers(self, topic_id: str, *, limit: int, offset: int) -> list[PaperSummary]:
        if not self.repository.exists(topic_id):
            raise DiscoveryNotFoundError("topic", topic_id)
        papers = self.repository.list_papers(topic_id, limit=limit, offset=offset)
        return [_build_paper_summary(paper) for paper in papers]
