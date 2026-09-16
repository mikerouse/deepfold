"""pipeline stages and parked flag

Revision ID: 002_pipeline
Revises: 001_initial
Create Date: 2026-09-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_pipeline"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "drafts",
        sa.Column("parked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute("UPDATE drafts SET status = 'checking' WHERE status = 'awaiting_review'")
    op.execute(
        "UPDATE drafts SET status = 'pitch' "
        "WHERE slug = 'midlands-councils-40m-social-care' AND status = 'checking'"
    )
    op.execute(
        "UPDATE drafts SET status = 'drafting' "
        "WHERE slug = 'nuneaton-camphill-burglary-appeal' AND status = 'checking'"
    )


def downgrade() -> None:
    op.execute("UPDATE drafts SET status = 'awaiting_review' WHERE status IN ('pitch', 'drafting', 'checking')")
    op.drop_column("drafts", "parked")
