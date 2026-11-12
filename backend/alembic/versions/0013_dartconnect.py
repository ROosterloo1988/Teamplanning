"""DartConnect: matches.dartconnect_url + teambeheer_configs liga-koppeling

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("dartconnect_url", sa.String(length=255), nullable=True))
    op.add_column(
        "teambeheer_configs", sa.Column("dartconnect_league", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "teambeheer_configs",
        sa.Column("last_dartconnect_sync_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "teambeheer_configs", sa.Column("last_dartconnect_sync_status", sa.String(length=20), nullable=True)
    )
    op.add_column("teambeheer_configs", sa.Column("last_dartconnect_sync_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("teambeheer_configs", "last_dartconnect_sync_message")
    op.drop_column("teambeheer_configs", "last_dartconnect_sync_status")
    op.drop_column("teambeheer_configs", "last_dartconnect_sync_at")
    op.drop_column("teambeheer_configs", "dartconnect_league")
    op.drop_column("matches", "dartconnect_url")
