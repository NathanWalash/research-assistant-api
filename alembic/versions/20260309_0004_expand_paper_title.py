"""Expand paper title column to text.

Revision ID: 20260309_0004
Revises: 20260309_0003
Create Date: 2026-03-09 17:40:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260309_0004"
down_revision: str | None = "20260309_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("papers") as batch_op:
        batch_op.alter_column(
            "title",
            existing_type=sa.String(length=512),
            type_=sa.Text(),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("papers") as batch_op:
        batch_op.alter_column(
            "title",
            existing_type=sa.Text(),
            type_=sa.String(length=512),
            existing_nullable=False,
        )
