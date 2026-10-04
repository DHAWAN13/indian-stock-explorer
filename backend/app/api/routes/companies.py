from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import (
    get_company_resolver,
    get_market_data_provider,
)
from app.api.schemas import (
    CompanyOverviewResponse,
    CompanyResearchListingResponse,
    CompanyResearchResponse,
    CompanySearchResponse,
    MarketQuoteResponse,
    SecurityResponse,
)
from app.domain.models import ResolutionStatus
from app.providers.market_data.base import (
    MarketDataProvider,
    MarketDataProviderError,
)
from app.services.company_resolver import CompanyResolver
from app.services.listing_verifier import verify_listing

router = APIRouter(prefix="/companies", tags=["companies"])


def to_security_response(security) -> SecurityResponse:
    return SecurityResponse(
        company_name=security.company_name,
        symbol=security.symbol,
        exchange=security.exchange,
        isin=security.isin,
        security_code=security.security_code,
    )


def to_quote_response(quote) -> MarketQuoteResponse:
    return MarketQuoteResponse(
        symbol=quote.symbol,
        exchange=quote.exchange,
        price=quote.price,
        previous_close=quote.previous_close,
        change=quote.change,
        change_percent=quote.change_percent,
        currency=quote.currency,
        timestamp=quote.timestamp,
        source=quote.source,
    )


@router.get("/search", response_model=CompanySearchResponse)
def search_company(
    q: str = Query(..., min_length=1, max_length=100),
    resolver: CompanyResolver = Depends(get_company_resolver),
) -> CompanySearchResponse:
    result = resolver.resolve(q)

    return CompanySearchResponse(
        query=result.query,
        resolution_status=result.status,
        matches=[
            to_security_response(security)
            for security in result.matches
        ],
    )


@router.get("/overview", response_model=CompanyOverviewResponse)
def get_company_overview(
    q: str = Query(..., min_length=1, max_length=100),
    resolver: CompanyResolver = Depends(get_company_resolver),
) -> CompanyOverviewResponse:
    result = resolver.resolve(q)
    listing_status = verify_listing(result)

    company_name = None
    if result.status == ResolutionStatus.RESOLVED and result.matches:
        company_name = max(
            result.matches,
            key=lambda security: len(security.company_name),
        ).company_name

    return CompanyOverviewResponse(
        query=result.query,
        resolution_status=result.status,
        listing_status=listing_status,
        company_name=company_name,
        listings=[
            to_security_response(security)
            for security in result.matches
        ],
    )


@router.get("/quote", response_model=MarketQuoteResponse)
def get_company_quote(
    symbol: str = Query(..., min_length=1, max_length=30),
    exchange: str = Query(..., pattern="^(NSE|BSE)$"),
    provider: MarketDataProvider = Depends(get_market_data_provider),
) -> MarketQuoteResponse:
    try:
        quote = provider.get_quote(symbol, exchange)
    except MarketDataProviderError as exc:
        raise HTTPException(
            status_code=503,
            detail="Market data is temporarily unavailable.",
        ) from exc

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail="No quote found for this symbol and exchange.",
        )

    return to_quote_response(quote)


@router.get("/research", response_model=CompanyResearchResponse)
def research_company(
    q: str = Query(..., min_length=1, max_length=100),
    resolver: CompanyResolver = Depends(get_company_resolver),
    provider: MarketDataProvider = Depends(get_market_data_provider),
) -> CompanyResearchResponse:
    result = resolver.resolve(q)
    listing_status = verify_listing(result)

    company_name = None
    if result.status == ResolutionStatus.RESOLVED and result.matches:
        company_name = max(
            result.matches,
            key=lambda security: len(security.company_name),
        ).company_name

    research_listings = []

    for security in result.matches:
        quote_response = None

        # Do not fetch quotes when the company identity is ambiguous.
        if result.status == ResolutionStatus.RESOLVED:
            try:
                quote = provider.get_quote(
                    security.symbol,
                    security.exchange,
                )
            except MarketDataProviderError as exc:
                raise HTTPException(
                    status_code=503,
                    detail="Market data is temporarily unavailable.",
                ) from exc

            if quote is not None:
                quote_response = to_quote_response(quote)

        research_listings.append(
            CompanyResearchListingResponse(
                listing=to_security_response(security),
                quote=quote_response,
            )
        )

    return CompanyResearchResponse(
        query=result.query,
        resolution_status=result.status,
        listing_status=listing_status,
        company_name=company_name,
        listings=research_listings,
    )