from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from research_assistant_api.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    projects: Mapped[list["Project"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    annotations: Mapped[list["Annotation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
