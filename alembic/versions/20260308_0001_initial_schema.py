"""create initial database schema

Revision ID: 20260308_0001
Revises:
Create Date: 2026-03-08 17:45:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260308_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_institutions")),
    )
    op.create_index(op.f("ix_institutions_name"), "institutions", ["name"], unique=False)

    op.create_table(
        "topics",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("field", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_topics")),
    )
    op.create_index(op.f("ix_topics_name"), "topics", ["name"], unique=False)

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "authors",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("orcid", sa.String(length=255), nullable=True),
        sa.Column("institution_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["institution_id"],
            ["institutions.id"],
            name=op.f("fk_authors_institution_id_institutions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_authors")),
        sa.UniqueConstraint("orcid", name=op.f("uq_authors_orcid")),
    )
    op.create_index(op.f("ix_authors_institution_id"), "authors", ["institution_id"], unique=False)
    op.create_index(op.f("ix_authors_name"), "authors", ["name"], unique=False)

    op.create_table(
        "papers",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("citation_count", sa.Integer(), nullable=False),
        sa.Column("doi", sa.String(length=255), nullable=True),
        sa.Column("journal", sa.String(length=255), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("work_type", sa.String(length=64), nullable=True),
        sa.Column("topic_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
            name=op.f("fk_papers_topic_id_topics"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_papers")),
        sa.UniqueConstraint("doi", name=op.f("uq_papers_doi")),
    )
    op.create_index(op.f("ix_papers_publication_year"), "papers", ["publication_year"], unique=False)
    op.create_index(op.f("ix_papers_title"), "papers", ["title"], unique=False)
    op.create_index(op.f("ix_papers_topic_id"), "papers", ["topic_id"], unique=False)

    op.create_table(
        "citations",
        sa.Column("citing_paper_id", sa.String(length=255), nullable=False),
        sa.Column("cited_paper_id", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["cited_paper_id"],
            ["papers.id"],
            name=op.f("fk_citations_cited_paper_id_papers"),
        ),
        sa.ForeignKeyConstraint(
            ["citing_paper_id"],
            ["papers.id"],
            name=op.f("fk_citations_citing_paper_id_papers"),
        ),
        sa.PrimaryKeyConstraint(
            "citing_paper_id",
            "cited_paper_id",
            name=op.f("pk_citations"),
        ),
    )

    op.create_table(
        "paper_authors",
        sa.Column("paper_id", sa.String(length=255), nullable=False),
        sa.Column("author_id", sa.String(length=255), nullable=False),
        sa.Column("author_position", sa.Integer(), nullable=True),
        sa.Column("is_corresponding", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["authors.id"],
            name=op.f("fk_paper_authors_author_id_authors"),
        ),
        sa.ForeignKeyConstraint(
            ["paper_id"],
            ["papers.id"],
            name=op.f("fk_paper_authors_paper_id_papers"),
        ),
        sa.PrimaryKeyConstraint("paper_id", "author_id", name=op.f("pk_paper_authors")),
    )

    op.create_table(
        "projects",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_projects_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
    )
    op.create_index(op.f("ix_projects_user_id"), "projects", ["user_id"], unique=False)

    op.create_table(
        "annotations",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("paper_id", sa.String(length=255), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["paper_id"],
            ["papers.id"],
            name=op.f("fk_annotations_paper_id_papers"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_annotations_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_annotations")),
    )
    op.create_index(op.f("ix_annotations_paper_id"), "annotations", ["paper_id"], unique=False)
    op.create_index(op.f("ix_annotations_user_id"), "annotations", ["user_id"], unique=False)

    op.create_table(
        "reading_list_items",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("paper_id", sa.String(length=255), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["paper_id"],
            ["papers.id"],
            name=op.f("fk_reading_list_items_paper_id_papers"),
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_reading_list_items_project_id_projects"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reading_list_items")),
        sa.UniqueConstraint("project_id", "paper_id", name=op.f("uq_reading_list_items_project_id")),
    )
    op.create_index(
        op.f("ix_reading_list_items_paper_id"),
        "reading_list_items",
        ["paper_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reading_list_items_project_id"),
        "reading_list_items",
        ["project_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_reading_list_items_project_id"), table_name="reading_list_items")
    op.drop_index(op.f("ix_reading_list_items_paper_id"), table_name="reading_list_items")
    op.drop_table("reading_list_items")

    op.drop_index(op.f("ix_annotations_user_id"), table_name="annotations")
    op.drop_index(op.f("ix_annotations_paper_id"), table_name="annotations")
    op.drop_table("annotations")

    op.drop_index(op.f("ix_projects_user_id"), table_name="projects")
    op.drop_table("projects")

    op.drop_table("paper_authors")
    op.drop_table("citations")

    op.drop_index(op.f("ix_papers_topic_id"), table_name="papers")
    op.drop_index(op.f("ix_papers_title"), table_name="papers")
    op.drop_index(op.f("ix_papers_publication_year"), table_name="papers")
    op.drop_table("papers")

    op.drop_index(op.f("ix_authors_name"), table_name="authors")
    op.drop_index(op.f("ix_authors_institution_id"), table_name="authors")
    op.drop_table("authors")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_topics_name"), table_name="topics")
    op.drop_table("topics")

    op.drop_index(op.f("ix_institutions_name"), table_name="institutions")
    op.drop_table("institutions")
