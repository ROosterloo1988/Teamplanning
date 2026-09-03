"""teambeheer_configs

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "teambeheer_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "season_id", sa.Integer(), sa.ForeignKey("seasons.id"), nullable=False, unique=True
        ),
        sa.Column("bond_id", sa.Integer(), nullable=False),
        sa.Column("poule", sa.String(20), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("team_naam", sa.String(120), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(20), nullable=True),
        sa.Column("last_sync_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("teambeheer_configs")
