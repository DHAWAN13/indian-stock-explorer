from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_company_resolver
from app.api.schemas import (
    CompanyOverviewResponse,
    CompanySearchResponse,
    SecurityResponse,
)
from app.domain.models import ResolutionStatus
from app.services.company_resolver import CompanyResolver

router = APIRouter(prefix="/companies", tags=["companies"])


def to_security_response(security) -> SecurityResponse:
    return SecurityResponse(
        company_name=security.company_name,
        symbol=security.symbol,
        exchange=security.exchange,
        isin=security.isin,
        security_code=security.security_code,
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

    company_name = None

    if result.status == ResolutionStatus.RESOLVED and result.matches:
        # Prefer the most descriptive exchange-provided name.
        company_name = max(
            result.matches,
            key=lambda security: len(security.company_name),
        ).company_name

    return CompanyOverviewResponse(
        query=result.query,
        resolution_status=result.status,
        company_name=company_name,
        listings=[
            to_security_response(security)
            for security in result.matches
        ],
    )