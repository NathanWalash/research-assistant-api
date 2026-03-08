from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from research_assistant_api.models import Paper, Topic


@dataclass(slots=True)
class TopicRecord:
    topic: Topic
    paper_count: int


class TopicRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_topics(self, *, limit: int, offset: int) -> list[TopicRecord]:
        statement = (
            select(Topic, func.count(Paper.id).label("paper_count"))
            .outerjoin(Paper, Paper.topic_id == Topic.id)
            .group_by(Topic.id)
            .order_by(func.count(Paper.id).desc(), Topic.name.asc())
            .offset(offset)
            .limit(limit)
        )
        return [TopicRecord(topic=row[0], paper_count=row[1]) for row in self.session.execute(statement)]

    def exists(self, topic_id: str) -> bool:
        statement = select(Topic.id).where(Topic.id == topic_id)
        return self.session.scalar(statement) is not None

    def list_papers(self, topic_id: str, *, limit: int, offset: int) -> list[Paper]:
        statement = (
            select(Paper)
            .options(selectinload(Paper.topic))
            .where(Paper.topic_id == topic_id)
            .order_by(Paper.publication_year.desc(), Paper.citation_count.desc(), Paper.title.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())
