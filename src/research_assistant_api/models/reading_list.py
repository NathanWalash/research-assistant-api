from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from research_assistant_api.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class ReadingListItem(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "reading_list_items"
    __table_args__ = (UniqueConstraint("project_id", "paper_id"),)

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="reading_list_items")
    paper: Mapped["Paper"] = relationship(back_populates="reading_list_items")
