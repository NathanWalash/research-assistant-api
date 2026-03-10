from dataclasses import dataclass

from sqlalchemy import Float, cast, func, select
from sqlalchemy.orm import Session, selectinload

from research_assistant_api.models import Paper, Topic


@dataclass(slots=True)
class TopicAnalyticsRecord:
    topic: Topic
    paper_count: int
    total_citation_count: int
    average_citation_count: float


@dataclass(slots=True)
class PublicationTrendRecord:
    publication_year: int
    paper_count: int
    total_citation_count: int
    average_citation_count: float


class AnalyticsRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_top_papers(
        self,
        *,
        topic: str | None,
        year: int | None,
        limit: int,
        offset: int,
    ) -> list[Paper]:
        statement = select(Paper).options(selectinload(Paper.topic))

        if topic:
            normalized_topic = topic.strip()
            statement = statement.join(Topic, Paper.topic_id == Topic.id).where(
                (Paper.topic_id == normalized_topic)
                | (func.lower(Topic.name) == normalized_topic.lower())
            )

        if year is not None:
            statement = statement.where(Paper.publication_year == year)

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

    def list_topic_distribution(
        self,
        *,
        year: int | None,
        limit: int,
        offset: int,
    ) -> list[TopicAnalyticsRecord]:
        statement = (
            select(
                Topic,
                func.count(Paper.id).label("paper_count"),
                func.coalesce(func.sum(Paper.citation_count), 0).label(
                    "total_citation_count"
                ),
                func.avg(cast(Paper.citation_count, Float)).label(
                    "average_citation_count"
                ),
            )
            .join(Paper, Paper.topic_id == Topic.id)
            .group_by(Topic.id)
        )

        if year is not None:
            statement = statement.where(Paper.publication_year == year)

        statement = (
            statement.order_by(
                func.count(Paper.id).desc(),
                func.coalesce(func.sum(Paper.citation_count), 0).desc(),
                Topic.name.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return [
            TopicAnalyticsRecord(
                topic=row[0],
                paper_count=row[1],
                total_citation_count=row[2],
                average_citation_count=float(row[3] or 0.0),
            )
            for row in self.session.execute(statement)
        ]

    def list_publication_trends(
        self,
        *,
        start_year: int | None,
        end_year: int | None,
    ) -> list[PublicationTrendRecord]:
        statement = select(
            Paper.publication_year,
            func.count(Paper.id).label("paper_count"),
            func.coalesce(func.sum(Paper.citation_count), 0).label(
                "total_citation_count"
            ),
            func.avg(cast(Paper.citation_count, Float)).label("average_citation_count"),
        )

        if start_year is not None:
            statement = statement.where(Paper.publication_year >= start_year)
        if end_year is not None:
            statement = statement.where(Paper.publication_year <= end_year)

        statement = statement.group_by(Paper.publication_year).order_by(
            Paper.publication_year.asc()
        )

        return [
            PublicationTrendRecord(
                publication_year=row[0],
                paper_count=row[1],
                total_citation_count=row[2],
                average_citation_count=float(row[3] or 0.0),
            )
            for row in self.session.execute(statement)
        ]
