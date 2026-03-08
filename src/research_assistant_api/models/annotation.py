from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from research_assistant_api.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from research_assistant_api.models.paper import Paper
    from research_assistant_api.models.user import User


class Annotation(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "annotations"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    paper_id: Mapped[str] = mapped_column(
        ForeignKey("papers.id"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship(back_populates="annotations")
    paper: Mapped[Paper] = relationship(back_populates="annotations")
