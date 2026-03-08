from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from research_assistant_api.db.base import Base

if TYPE_CHECKING:
    from research_assistant_api.models.annotation import Annotation
    from research_assistant_api.models.author import PaperAuthor
    from research_assistant_api.models.citation import Citation
    from research_assistant_api.models.reading_list import ReadingListItem
    from research_assistant_api.models.topic import Topic


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    publication_date: Mapped[date | None] = mapped_column(nullable=True)
    citation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    journal: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    work_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    topic_id: Mapped[str | None] = mapped_column(
        ForeignKey("topics.id"),
        nullable=True,
        index=True,
    )

    topic: Mapped[Topic | None] = relationship(back_populates="papers")
    authorships: Mapped[list[PaperAuthor]] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
    )
    outgoing_citations: Mapped[list[Citation]] = relationship(
        back_populates="citing_paper",
        cascade="all, delete-orphan",
        foreign_keys="Citation.citing_paper_id",
    )
    incoming_citations: Mapped[list[Citation]] = relationship(
        back_populates="cited_paper",
        cascade="all, delete-orphan",
        foreign_keys="Citation.cited_paper_id",
    )
    reading_list_items: Mapped[list[ReadingListItem]] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
    )
    annotations: Mapped[list[Annotation]] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
    )
