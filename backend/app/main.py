from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes import (
    admin,
    audit,
    auth,
    availability,
    lineups,
    matches,
    notifications,
    players,
    push,
    seasons,
    stats,
    teambeheer,
)
from app.core.config import settings
from app.db.session import get_db

# Zorgt dat alle modellen bij startup geregistreerd zijn bij SQLAlchemy's
# mapper-registry — anders faalt een relationship() naar een model dat geen
# enkele routemodule zelf importeert (bv. Season.competitions -> Competition,
# waarvoor geen route bestaat) pas bij de eerste query die de mapper
# configureert, in plaats van meteen bij het opstarten.
import app.db.base  # noqa: F401,E402
from app.services.scheduler import start_scheduler, stop_scheduler  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(players.router, prefix=settings.API_V1_PREFIX)
app.include_router(seasons.router, prefix=settings.API_V1_PREFIX)
app.include_router(matches.router, prefix=settings.API_V1_PREFIX)
app.include_router(availability.router, prefix=settings.API_V1_PREFIX)
app.include_router(lineups.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(audit.router, prefix=settings.API_V1_PREFIX)
app.include_router(stats.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)
app.include_router(push.router, prefix=settings.API_V1_PREFIX)
app.include_router(teambeheer.router, prefix=settings.API_V1_PREFIX)


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    """Doet een echte databasequery, niet alleen 'is het proces gestart' —
    anders blijft dit 'ok' zeggen terwijl Postgres onbereikbaar is, wat het
    onbruikbaar maakt voor monitoring."""
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
