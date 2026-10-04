from app.domain.models import (
    ListingStatus,
    ResolutionResult,
    ResolutionStatus,
    Security,
)
from app.services.listing_verifier import verify_listing


SECURITY = Security(
    company_name="Tata Motors Limited",
    symbol="TMCV",
    exchange="NSE",
    isin="INE1TAE01010",
)


def test_verified_match_is_listed():
    result = ResolutionResult(
        query="TMCV",
        status=ResolutionStatus.RESOLVED,
        matches=[SECURITY],
    )

    assert verify_listing(result) == ListingStatus.LISTED


def test_no_match_with_available_data_is_not_listed():
    result = ResolutionResult(
        query="Unknown Company",
        status=ResolutionStatus.NOT_FOUND,
        matches=[],
    )

    assert verify_listing(result) == ListingStatus.NOT_LISTED


def test_unavailable_exchange_data_is_unverified():
    result = ResolutionResult(
        query="Unknown Company",
        status=ResolutionStatus.NOT_FOUND,
        matches=[],
    )

    assert (
        verify_listing(result, exchange_data_available=False)
        == ListingStatus.UNVERIFIED
    )


def test_ambiguous_company_is_unverified():
    result = ResolutionResult(
        query="Tata Motors",
        status=ResolutionStatus.AMBIGUOUS,
        matches=[SECURITY],
    )

    assert verify_listing(result) == ListingStatus.UNVERIFIED