"""matches.datum_onbekend (wedstrijd weer n.n.b. na eerder wel een datum)

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column("datum_onbekend", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("matches", "datum_onbekend", server_default=None)


def downgrade() -> None:
    op.drop_column("matches", "datum_onbekend")
