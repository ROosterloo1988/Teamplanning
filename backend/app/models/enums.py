import enum


class UserRole(str, enum.Enum):
    SPELER = "SPELER"
    CAPTAIN = "CAPTAIN"
    BEHEER = "BEHEER"


class MatchType(str, enum.Enum):
    COMPETITIE = "COMPETITIE"
    BEKER = "BEKER"
    INHAAL = "INHAAL"
    OVERIG = "OVERIG"


class MatchStatus(str, enum.Enum):
    GEPLAND = "GEPLAND"
    GESPEELD = "GESPEELD"
    AFGELAST = "AFGELAST"


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    IF_NEEDED = "IF_NEEDED"
    NO_RESPONSE = "NO_RESPONSE"
