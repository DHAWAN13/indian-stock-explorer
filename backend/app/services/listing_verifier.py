from app.domain.models import (
    ListingStatus,
    ResolutionResult,
    ResolutionStatus,
)


def verify_listing(
    result: ResolutionResult,
    exchange_data_available: bool = True,
) -> ListingStatus:
    if not exchange_data_available:
        return ListingStatus.UNVERIFIED

    if result.status == ResolutionStatus.NOT_FOUND:
        return ListingStatus.NOT_LISTED

    if result.status == ResolutionStatus.RESOLVED and result.matches:
        return ListingStatus.LISTED

    # An ambiguous company name cannot verify which company the user means.
    return ListingStatus.UNVERIFIED