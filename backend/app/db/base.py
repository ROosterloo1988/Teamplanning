# Import Base and all models so Alembic autogenerate and metadata.create_all see them.
from app.db.base_class import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.team import Team  # noqa: F401
from app.models.player import Player  # noqa: F401
from app.models.season import Season  # noqa: F401
from app.models.competition import Competition  # noqa: F401
from app.models.match import Match  # noqa: F401
from app.models.availability import Availability  # noqa: F401
from app.models.lineup import Lineup, LineupPlayer  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.teambeheer import TeambeheerConfig  # noqa: F401
