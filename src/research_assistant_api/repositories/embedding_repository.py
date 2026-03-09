from sqlalchemy import select
from sqlalchemy.orm import Session

from research_assistant_api.models import Paper


class EmbeddingRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_papers_for_embedding(
        self,
        *,
        limit: int | None,
        paper_id: str | None,
        missing_only: bool,
    ) -> list[Paper]:
        statement = select(Paper).order_by(
            Paper.publication_year.desc(),
            Paper.title.asc(),
        )

        if paper_id is not None:
            statement = statement.where(Paper.id == paper_id)
        if missing_only:
            statement = statement.where(Paper.embedding.is_(None))
        if limit is not None:
            statement = statement.limit(limit)

        return list(self.session.scalars(statement).all())

    def save_embeddings(self, papers: list[Paper], embeddings: list[list[float]]) -> None:
        for paper, embedding in zip(papers, embeddings):
            paper.embedding = embedding
            self.session.add(paper)
        self.session.commit()
