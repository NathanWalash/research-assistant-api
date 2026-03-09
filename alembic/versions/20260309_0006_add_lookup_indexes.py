"""Add citation lookup indexes and pgvector ANN index.

Revision ID: 20260309_0006
Revises: 20260309_0005
Create Date: 2026-03-09 23:15:00
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260309_0006"
down_revision: str | None = "20260309_0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    op.create_index(
        op.f("ix_citations_citing_paper_id"),
        "citations",
        ["citing_paper_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_citations_cited_paper_id"),
        "citations",
        ["cited_paper_id"],
        unique=False,
    )

    if dialect_name == "postgresql":
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_papers_embedding_ivfflat
            ON papers
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
            WHERE embedding IS NOT NULL
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_papers_embedding_ivfflat")

    op.drop_index(op.f("ix_citations_cited_paper_id"), table_name="citations")
    op.drop_index(op.f("ix_citations_citing_paper_id"), table_name="citations")
