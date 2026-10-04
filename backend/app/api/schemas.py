from pydantic import BaseModel

from app.domain.models import ResolutionStatus


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
    company_name: str | None = None
    listings: list[SecurityResponse]