from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel

from app.domain.models import ListingStatus, ResolutionStatus


class SecurityResponse(BaseModel):
    company_name: str
    symbol: str
    exchange: str
    isin: str | None = None
    security_code: str | None = None


class CompanySearchResponse(BaseModel):
    query: str
    resolution_status: ResolutionStatus
    matches: list[SecurityResponse]


class CompanyOverviewResponse(BaseModel):
    query: str
    resolution_status: ResolutionStatus
    listing_status: ListingStatus
    company_name: str | None = None
    listings: list[SecurityResponse]


class MarketQuoteResponse(BaseModel):
    symbol: str
    exchange: str
    price: Decimal
    previous_close: Decimal
    change: Decimal
    change_percent: Decimal
    currency: str
    timestamp: datetime
    source: str
    as_of: datetime
    freshness: Literal["fresh", "stale"]


class CompanyResearchListingResponse(BaseModel):
    listing: SecurityResponse
    quote: MarketQuoteResponse | None = None


class CompanyResearchResponse(BaseModel):
    query: str
    resolution_status: ResolutionStatus
    listing_status: ListingStatus
    company_name: str | None = None
    listings: list[CompanyResearchListingResponse]


class HistoricalPriceBarResponse(BaseModel):
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int | None = None


class HistoricalPriceResponse(BaseModel):
    symbol: str
    exchange: str
    range: Literal["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "MAX"]
    source: str
    bars: list[HistoricalPriceBarResponse]