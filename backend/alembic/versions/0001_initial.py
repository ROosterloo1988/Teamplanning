"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# create_type=False: de enum-types worden hieronder expliciet aangemaakt/
# verwijderd (met checkfirst) zodat er precies één CREATE TYPE per naam
# gebeurt. Zonder create_type=False emit SQLAlchemy zelf óók een CREATE
# TYPE per kolom die de enum gebruikt, wat botst met de eigen aanmaak.
# Let op: dit moet de dialect-specifieke postgresql.ENUM zijn — de
# generieke sa.Enum() negeert create_type stilletjes.
user_role = ENUM("SPELER", "CAPTAIN", "BEHEER", name="userrole", create_type=False)
match_type = ENUM(
    "COMPETITIE", "BEKER", "INHAAL", "OVERIG", name="matchtype", create_type=False
)
match_status = ENUM("GEPLAND", "GESPEELD", "AFGELAST", name="matchstatus", create_type=False)
availability_status = ENUM(
    "AVAILABLE",
    "UNAVAILABLE",
    "IF_NEEDED",
    "NO_RESPONSE",
    name="availabilitystatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    match_type.create(bind, checkfirst=True)
    match_status.create(bind, checkfirst=True)
    availability_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("naam", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("rol", user_role, nullable=False, server_default="SPELER"),
        sa.Column("actief", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("naam", sa.String(120), nullable=False),
        sa.Column("vereniging", sa.String(120), nullable=True),
    )

    op.create_table(
        "seasons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("naam", sa.String(50), nullable=False),
        sa.Column("startjaar", sa.Integer(), nullable=False),
        sa.Column("eindjaar", sa.Integer(), nullable=False),
    )

    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, unique=True),
        sa.Column("naam", sa.String(120), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=True),
    )

    op.create_table(
        "competitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("season_id", sa.Integer(), sa.ForeignKey("seasons.id"), nullable=False),
        sa.Column("naam", sa.String(120), nullable=False),
        sa.Column("poule", sa.String(50), nullable=True),
    )

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(100), nullable=True, unique=True),
        sa.Column("season_id", sa.Integer(), sa.ForeignKey("seasons.id"), nullable=True),
        sa.Column("type", match_type, nullable=False, server_default="COMPETITIE"),
        sa.Column("nummer", sa.String(20), nullable=True),
        sa.Column("datum", sa.Date(), nullable=False),
        sa.Column("tijd", sa.Time(), nullable=True),
        sa.Column("thuisteam", sa.String(120), nullable=False),
        sa.Column("uitteam", sa.String(120), nullable=False),
        sa.Column("locatie", sa.String(120), nullable=True),
        sa.Column("status", match_status, nullable=False, server_default="GEPLAND"),
    )
    op.create_index("ix_matches_external_id", "matches", ["external_id"])

    op.create_table(
        "availability",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("status", availability_status, nullable=False, server_default="NO_RESPONSE"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("match_id", "player_id", name="uq_availability_match_player"),
    )

    op.create_table(
        "lineups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("matches.id"), nullable=False, unique=True),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "lineup_players",
        sa.Column("lineup_id", sa.Integer(), sa.ForeignKey("lineups.id"), primary_key=True),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), primary_key=True),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("lineup_players")
    op.drop_table("lineups")
    op.drop_table("availability")
    op.drop_index("ix_matches_external_id", table_name="matches")
    op.drop_table("matches")
    op.drop_table("competitions")
    op.drop_table("players")
    op.drop_table("seasons")
    op.drop_table("teams")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    availability_status.drop(bind, checkfirst=True)
    match_status.drop(bind, checkfirst=True)
    match_type.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
