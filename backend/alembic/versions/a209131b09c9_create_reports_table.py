"""create reports table

Revision ID: a209131b09c9
Revises:
Create Date: 2026-01-25 19:27:58.169602

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a209131b09c9"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_url", sa.Text(), nullable=False),
        sa.Column("repo_owner", sa.Text(), nullable=True),
        sa.Column("repo_name", sa.Text(), nullable=True),
        sa.Column("commit_sha", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("findings_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("reports")
