"""remove unused multi-team scaffolding (teams table, players.team_id)

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("players_team_id_fkey", "players", type_="foreignkey")
    op.drop_column("players", "team_id")
    op.drop_table("teams")


def downgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("naam", sa.String(120), nullable=False),
        sa.Column("vereniging", sa.String(120), nullable=True),
    )
    op.add_column("players", sa.Column("team_id", sa.Integer(), nullable=True))
    op.create_foreign_key("players_team_id_fkey", "players", "teams", ["team_id"], ["id"])
