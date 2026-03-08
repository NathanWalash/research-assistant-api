from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from research_assistant_api.db.base import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    field: Mapped[str | None] = mapped_column(String(255), nullable=True)

    papers: Mapped[list["Paper"]] = relationship(back_populates="topic")
