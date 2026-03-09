"""Drop overly strict unique constraint on author ORCID.

Revision ID: 20260309_0003
Revises: 20260309_0002
Create Date: 2026-03-09 17:20:00
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260309_0003"
down_revision: str | None = "20260309_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("authors") as batch_op:
        batch_op.drop_constraint(op.f("uq_authors_orcid"), type_="unique")


def downgrade() -> None:
    with op.batch_alter_table("authors") as batch_op:
        batch_op.create_unique_constraint(op.f("uq_authors_orcid"), ["orcid"])
