"""add paper embeddings

Revision ID: 20260309_0002
Revises: 20260308_0001
Create Date: 2026-03-09 10:30:00
"""

from collections.abc import Sequence

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa

from research_assistant_api.embeddings.service import EMBEDDING_DIMENSIONS

# revision identifiers, used by Alembic.
revision: str = "20260309_0002"
down_revision: str | None = "20260308_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.add_column(
            "papers",
            sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=True),
        )
        return

    op.add_column(
        "papers",
        sa.Column("embedding", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("papers", "embedding")
