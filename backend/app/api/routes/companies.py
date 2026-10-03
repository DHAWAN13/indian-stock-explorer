from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_company_resolver
from app.api.schemas import CompanySearchResponse, SecurityResponse
from app.services.company_resolver import CompanyResolver

router = APIRouter(prefix="/companies", tags=["companies"])


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
            SecurityResponse(
                company_name=security.company_name,
                symbol=security.symbol,
                exchange=security.exchange,
                isin=security.isin,
                security_code=security.security_code,
            )
            for security in result.matches
        ],
    )