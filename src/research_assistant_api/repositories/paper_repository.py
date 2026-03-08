from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from research_assistant_api.models import Author, Paper, PaperAuthor, Topic


class PaperRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, paper_id: str) -> Paper | None:
        statement = (
            select(Paper)
            .options(
                selectinload(Paper.topic),
                selectinload(Paper.authorships)
                .selectinload(PaperAuthor.author)
                .selectinload(Author.institution),
            )
            .where(Paper.id == paper_id)
        )
        return self.session.scalar(statement)

    def search(
        self,
        *,
        query: str | None,
        topic: str | None,
        year: int | None,
        citation_count: int | None,
        limit: int,
        offset: int,
    ) -> list[Paper]:
        statement = select(Paper).options(selectinload(Paper.topic))

        if topic:
            normalized_topic = topic.strip()
            statement = statement.join(Topic, Paper.topic_id == Topic.id, isouter=True).where(
                or_(
                    Paper.topic_id == normalized_topic,
                    func.lower(Topic.name) == normalized_topic.lower(),
                )
            )

        if query:
            pattern = f"%{query.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(Paper.title).like(pattern),
                    func.lower(Paper.abstract).like(pattern),
                )
            )

        if year is not None:
            statement = statement.where(Paper.publication_year == year)

        if citation_count is not None:
            statement = statement.where(Paper.citation_count >= citation_count)

        statement = (
            statement.order_by(
                Paper.citation_count.desc(),
                Paper.publication_year.desc(),
                Paper.title.asc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())
