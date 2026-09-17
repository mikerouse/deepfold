"""media asset url + prompt_version

Revision ID: 004_media_url
Revises: 003_jobs_packages
Create Date: 2026-09-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_media_url"
down_revision: Union[str, None] = "003_jobs_packages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("media_assets", sa.Column("url", sa.String(length=1024), nullable=False, server_default=""))
    op.add_column(
        "media_assets",
        sa.Column("prompt_version", sa.String(length=64), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("media_assets", "prompt_version")
    op.drop_column("media_assets", "url")
