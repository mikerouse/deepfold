"""jobs, outlet packages, county + geography

Revision ID: 003_jobs_packages
Revises: 002_pipeline
Create Date: 2026-09-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_jobs_packages"
down_revision: Union[str, None] = "002_pipeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("outlets", sa.Column("county", sa.String(length=128), nullable=False, server_default=""))
    op.add_column("drafts", sa.Column("geography", sa.JSON(), nullable=True))

    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("draft_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("worker", sa.String(length=255), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["draft_id"], ["drafts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_draft_id", "jobs", ["draft_id"], unique=False)
    op.create_index("ix_jobs_kind", "jobs", ["kind"], unique=False)
    op.create_index("ix_jobs_status", "jobs", ["status"], unique=False)

    op.create_table(
        "outlet_packages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("region", sa.String(length=128), nullable=False),
        sa.Column("county", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outlet_packages_slug", "outlet_packages", ["slug"], unique=True)

    op.create_table(
        "outlet_package_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("package_id", sa.Uuid(), nullable=False),
        sa.Column("outlet_id", sa.Uuid(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["outlet_packages.id"]),
        sa.ForeignKeyConstraint(["outlet_id"], ["outlets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("package_id", "outlet_id"),
    )
    op.create_index("ix_outlet_package_members_package_id", "outlet_package_members", ["package_id"], unique=False)
    op.create_index("ix_outlet_package_members_outlet_id", "outlet_package_members", ["outlet_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_outlet_package_members_outlet_id", table_name="outlet_package_members")
    op.drop_index("ix_outlet_package_members_package_id", table_name="outlet_package_members")
    op.drop_table("outlet_package_members")
    op.drop_index("ix_outlet_packages_slug", table_name="outlet_packages")
    op.drop_table("outlet_packages")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_kind", table_name="jobs")
    op.drop_index("ix_jobs_draft_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_column("drafts", "geography")
    op.drop_column("outlets", "county")
