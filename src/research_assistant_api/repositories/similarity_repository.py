from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from research_assistant_api.embeddings import cosine_similarity
from research_assistant_api.models import Paper


@dataclass(slots=True)
class SimilarPaperRecord:
    paper: Paper
    similarity_score: float


class SimilarityRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, paper_id: str) -> Paper | None:
        statement = (
            select(Paper)
            .options(selectinload(Paper.topic))
            .where(Paper.id == paper_id)
        )
        return self.session.scalar(statement)

    def list_similar(
        self,
        target_paper: Paper,
        *,
        limit: int,
        offset: int,
    ) -> list[SimilarPaperRecord]:
        if target_paper.embedding is None:
            return []

        if self.session.bind is not None and self.session.bind.dialect.name == "postgresql":
            distance = Paper.embedding.cosine_distance(target_paper.embedding)
            similarity = (1 - distance).label("similarity_score")
            statement = (
                select(Paper, similarity)
                .options(selectinload(Paper.topic))
                .where(
                    Paper.id != target_paper.id,
                    Paper.embedding.is_not(None),
                )
                .order_by(
                    distance.asc(),
                    Paper.citation_count.desc(),
                    Paper.publication_year.desc(),
                    Paper.title.asc(),
                )
                .offset(offset)
                .limit(limit)
            )
            return [
                SimilarPaperRecord(paper=row[0], similarity_score=float(row[1]))
                for row in self.session.execute(statement)
            ]

        statement = (
            select(Paper)
            .options(selectinload(Paper.topic))
            .where(
                Paper.id != target_paper.id,
                Paper.embedding.is_not(None),
            )
        )
        candidates = list(self.session.scalars(statement).all())
        ranked_candidates = sorted(
            (
                SimilarPaperRecord(
                    paper=candidate,
                    similarity_score=cosine_similarity(
                        target_paper.embedding,
                        candidate.embedding or [],
                    ),
                )
                for candidate in candidates
            ),
            key=lambda record: (
                -record.similarity_score,
                -record.paper.citation_count,
                -record.paper.publication_year,
                record.paper.title,
            ),
        )
        return ranked_candidates[offset : offset + limit]
