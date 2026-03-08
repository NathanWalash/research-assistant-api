from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from research_assistant_api.models import Author, Paper, PaperAuthor


@dataclass(slots=True)
class AuthorRecord:
    author: Author
    paper_count: int


class AuthorRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, author_id: str) -> AuthorRecord | None:
        statement = (
            select(Author, func.count(PaperAuthor.paper_id).label("paper_count"))
            .outerjoin(PaperAuthor, PaperAuthor.author_id == Author.id)
            .options(selectinload(Author.institution))
            .where(Author.id == author_id)
            .group_by(Author.id)
        )
        row = self.session.execute(statement).one_or_none()
        if row is None:
            return None
        return AuthorRecord(author=row[0], paper_count=row[1])

    def list_papers(self, author_id: str, *, limit: int, offset: int) -> list[Paper]:
        statement = (
            select(Paper)
            .join(PaperAuthor, PaperAuthor.paper_id == Paper.id)
            .options(selectinload(Paper.topic))
            .where(PaperAuthor.author_id == author_id)
            .order_by(Paper.publication_year.desc(), Paper.citation_count.desc(), Paper.title.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())
