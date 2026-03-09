from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from research_assistant_api.db.base import Base

if TYPE_CHECKING:
    from research_assistant_api.models.paper import Paper


class Citation(Base):
    __tablename__ = "citations"

    citing_paper_id: Mapped[str] = mapped_column(
        ForeignKey("papers.id"),
        primary_key=True,
        index=True,
    )
    cited_paper_id: Mapped[str] = mapped_column(
        ForeignKey("papers.id"),
        primary_key=True,
        index=True,
    )

    citing_paper: Mapped[Paper] = relationship(
        back_populates="outgoing_citations",
        foreign_keys=[citing_paper_id],
    )
    cited_paper: Mapped[Paper] = relationship(
        back_populates="incoming_citations",
        foreign_keys=[cited_paper_id],
    )
