"""Drop overly strict unique constraint on paper DOI.

Revision ID: 20260309_0005
Revises: 20260309_0004
Create Date: 2026-03-09 18:00:00
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260309_0005"
down_revision: str | None = "20260309_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("papers") as batch_op:
        batch_op.drop_constraint(op.f("uq_papers_doi"), type_="unique")


def downgrade() -> None:
    with op.batch_alter_table("papers") as batch_op:
        batch_op.create_unique_constraint(op.f("uq_papers_doi"), ["doi"])
