"""repair seasons.eindjaar (must always be startjaar + 1)

Een verkeerd ingevoerd eindjaar (bv. leeg/0 door een formulierfout) liet
resolve_year() in de teambeheer-sync stilzwijgend "geen datum" teruggeven
voor elke wedstrijd na de jaarwisseling (januari e.v.), omdat date(eindjaar,
maand, dag) een ValueError gaf. eindjaar is nu niet meer los instelbaar (zie
schemas/season.py); deze migratie repareert bestaande rijen zodat het
seizoen weer klopt.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-04

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE seasons SET eindjaar = startjaar + 1 WHERE eindjaar != startjaar + 1")


def downgrade() -> None:
    # Niet omkeerbaar: de oorspronkelijke (mogelijk foutieve) eindjaar-waarden
    # zijn niet bewaard.
    pass
