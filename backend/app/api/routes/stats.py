from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_captain
from app.db.session import get_db
from app.models.availability import Availability
from app.models.enums import AvailabilityStatus
from app.models.lineup import Lineup, LineupPlayer
from app.models.match import Match
from app.models.player import Player
from app.schemas.stats import PlayerStatsOut

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/players", response_model=list[PlayerStatsOut], dependencies=[Depends(require_captain)])
def player_stats(season_id: int | None = None, db: Session = Depends(get_db)):
    """Betere statistieken per speler, zie functioneel ontwerp v1 sectie 12/16.

    Optioneel filterbaar op seizoen (season_id) voor wedstrijdhistorie per seizoen.
    """
    players = db.query(Player).order_by(Player.naam).all()

    availability_query = db.query(Availability.player_id, Availability.status, func.count())
    lineup_query = db.query(LineupPlayer.player_id, func.count())
    if season_id is not None:
        availability_query = availability_query.join(Match, Availability.match_id == Match.id).filter(
            Match.season_id == season_id
        )
        lineup_query = (
            lineup_query.join(Lineup, LineupPlayer.lineup_id == Lineup.id)
            .join(Match, Lineup.match_id == Match.id)
            .filter(Match.season_id == season_id)
        )

    counts_by_player: dict[int, dict[AvailabilityStatus, int]] = {}
    for player_id, status_value, count in availability_query.group_by(
        Availability.player_id, Availability.status
    ).all():
        counts_by_player.setdefault(player_id, {})[status_value] = count

    lineup_counts = dict(lineup_query.group_by(LineupPlayer.player_id).all())

    result: list[PlayerStatsOut] = []
    for player in players:
        counts = counts_by_player.get(player.id, {})
        beschikbaar = counts.get(AvailabilityStatus.AVAILABLE, 0)
        niet_beschikbaar = counts.get(AvailabilityStatus.UNAVAILABLE, 0)
        indien_nodig = counts.get(AvailabilityStatus.IF_NEEDED, 0)
        geen_antwoord = counts.get(AvailabilityStatus.NO_RESPONSE, 0)
        totaal = beschikbaar + niet_beschikbaar + indien_nodig + geen_antwoord
        beantwoord = totaal - geen_antwoord
        response_rate = round((beantwoord / totaal) * 100, 1) if totaal else 0.0

        result.append(
            PlayerStatsOut(
                player_id=player.id,
                player_naam=player.naam,
                totaal=totaal,
                beschikbaar=beschikbaar,
                niet_beschikbaar=niet_beschikbaar,
                indien_nodig=indien_nodig,
                geen_antwoord=geen_antwoord,
                response_rate=response_rate,
                keer_opgesteld=lineup_counts.get(player.id, 0),
            )
        )
    return result
