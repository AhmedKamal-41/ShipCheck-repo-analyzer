"""add findings_v2 column

Revision ID: 13909e2a60b7
Revises: a209131b09c9
Create Date: 2026-04-25 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "13909e2a60b7"
down_revision: Union[str, Sequence[str], None] = "a209131b09c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column(
            "findings_v2",
            postgresql.JSONB().with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    with op.batch_alter_table("reports") as batch:
        batch.drop_column("findings_v2")
