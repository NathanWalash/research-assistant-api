from dataclasses import dataclass

from sqlalchemy import Float, and_, cast, func, select
from sqlalchemy.orm import Session, aliased, selectinload

from research_assistant_api.models import Author, Paper, PaperAuthor, Topic


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


@dataclass(slots=True)
class CollaborationPairRecord:
    author_a_id: str
    author_a_name: str
    author_b_id: str
    author_b_name: str
    shared_paper_count: int


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

    def list_collaboration_pairs(
        self,
        *,
        min_shared_papers: int,
        limit: int,
        offset: int,
    ) -> list[CollaborationPairRecord]:
        left_authorship = aliased(PaperAuthor)
        right_authorship = aliased(PaperAuthor)
        left_author = aliased(Author)
        right_author = aliased(Author)

        shared_paper_count = func.count(func.distinct(left_authorship.paper_id))

        statement = (
            select(
                left_author.id,
                left_author.name,
                right_author.id,
                right_author.name,
                shared_paper_count.label("shared_paper_count"),
            )
            .select_from(left_authorship)
            .join(
                right_authorship,
                and_(
                    left_authorship.paper_id == right_authorship.paper_id,
                    left_authorship.author_id < right_authorship.author_id,
                ),
            )
            .join(left_author, left_author.id == left_authorship.author_id)
            .join(right_author, right_author.id == right_authorship.author_id)
            .group_by(
                left_author.id,
                left_author.name,
                right_author.id,
                right_author.name,
            )
            .having(shared_paper_count >= min_shared_papers)
            .order_by(
                shared_paper_count.desc(),
                left_author.name.asc(),
                right_author.name.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return [
            CollaborationPairRecord(
                author_a_id=row[0],
                author_a_name=row[1],
                author_b_id=row[2],
                author_b_name=row[3],
                shared_paper_count=row[4],
            )
            for row in self.session.execute(statement)
        ]
