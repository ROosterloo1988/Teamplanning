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


# Mapping from legacy Excel cell values to the new availability status,
# per functioneel ontwerp v1 section 4 (hoofdletter-ongevoelig).
EXCEL_AVAILABILITY_MAP = {
    "v": AvailabilityStatus.AVAILABLE,
    "x": AvailabilityStatus.UNAVAILABLE,
    "?": AvailabilityStatus.IF_NEEDED,
    "1": AvailabilityStatus.AVAILABLE,  # opgesteld impliceert beschikbaar
    "": AvailabilityStatus.NO_RESPONSE,
}
