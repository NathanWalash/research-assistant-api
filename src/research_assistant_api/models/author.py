from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from research_assistant_api.db.base import Base

if TYPE_CHECKING:
    from research_assistant_api.models.paper import Paper


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)

    authors: Mapped[list["Author"]] = relationship(back_populates="institution")


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    orcid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    institution_id: Mapped[str | None] = mapped_column(
        ForeignKey("institutions.id"),
        nullable=True,
        index=True,
    )

    institution: Mapped[Institution | None] = relationship(back_populates="authors")
    paper_authorships: Mapped[list["PaperAuthor"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )


class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), primary_key=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("authors.id"), primary_key=True)
    author_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_corresponding: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    paper: Mapped[Paper] = relationship(back_populates="authorships")
    author: Mapped[Author] = relationship(back_populates="paper_authorships")
