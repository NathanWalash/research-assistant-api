from datetime import date

from pydantic import BaseModel, ConfigDict


class InstitutionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    country: str | None = None


class TopicSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    field: str | None = None


class PaperSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    publication_year: int
    publication_date: date | None = None
    citation_count: int
    doi: str | None = None
    journal: str | None = None
    language: str | None = None
    work_type: str | None = None
    topic: TopicSummary | None = None


class PaperAuthorSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    orcid: str | None = None
    institution: InstitutionSummary | None = None
    author_position: int | None = None
    is_corresponding: bool


class PaperDetail(PaperSummary):
    abstract: str | None = None
    authors: list[PaperAuthorSummary]


class AuthorDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    orcid: str | None = None
    institution: InstitutionSummary | None = None
    paper_count: int


class TopicListItem(TopicSummary):
    paper_count: int
