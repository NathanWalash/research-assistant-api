from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from research_assistant_api.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class Project(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "projects"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="projects")
    reading_list_items: Mapped[list["ReadingListItem"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
