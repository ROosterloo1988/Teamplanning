"""matches.uitslag_url (link naar wedstrijdformulier)

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("uitslag_url", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "uitslag_url")
