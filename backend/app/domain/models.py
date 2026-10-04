from dataclasses import dataclass
from enum import Enum


class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_FOUND = "NOT_FOUND"


@dataclass(frozen=True)
class Security:
    company_name: str
    symbol: str
    exchange: str
    isin: str | None = None
    security_code: str | None = None


@dataclass(frozen=True)
class ResolutionResult:
    query: str
    status: ResolutionStatus
    matches: list[Security]

class ListingStatus(str, Enum):
    LISTED = "LISTED"
    NOT_LISTED = "NOT_LISTED"
    UNVERIFIED = "UNVERIFIED"