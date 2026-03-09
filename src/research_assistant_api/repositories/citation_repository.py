from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from research_assistant_api.models import Citation, Paper


class CitationRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_cited_papers(
        self,
        paper_id: str,
        *,
        limit: int,
        offset: int,
    ) -> list[Paper]:
        statement = (
            select(Paper)
            .join(Citation, Paper.id == Citation.cited_paper_id)
            .options(selectinload(Paper.topic))
            .where(Citation.citing_paper_id == paper_id)
            .order_by(
                Paper.citation_count.desc(),
                Paper.publication_year.desc(),
                Paper.title.asc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def list_citing_papers(
        self,
        paper_id: str,
        *,
        limit: int,
        offset: int,
    ) -> list[Paper]:
        statement = (
            select(Paper)
            .join(Citation, Paper.id == Citation.citing_paper_id)
            .options(selectinload(Paper.topic))
            .where(Citation.cited_paper_id == paper_id)
            .order_by(
                Paper.citation_count.desc(),
                Paper.publication_year.desc(),
                Paper.title.asc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def list_outgoing_edges(
        self,
        paper_ids: Sequence[str],
    ) -> list[tuple[str, str]]:
        if not paper_ids:
            return []

        statement = select(Citation.citing_paper_id, Citation.cited_paper_id).where(
            Citation.citing_paper_id.in_(paper_ids)
        )
        return list(self.session.execute(statement).all())

    def list_papers_by_ids(self, paper_ids: Sequence[str]) -> list[Paper]:
        if not paper_ids:
            return []

        statement = (
            select(Paper)
            .options(selectinload(Paper.topic))
            .where(Paper.id.in_(paper_ids))
        )
        return list(self.session.scalars(statement).all())
