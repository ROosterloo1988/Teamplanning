"""matches.dartconnect_completed (live vs recap-label, los van onze eigen uitslag)

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column("dartconnect_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("matches", "dartconnect_completed", server_default=None)


def downgrade() -> None:
    op.drop_column("matches", "dartconnect_completed")
