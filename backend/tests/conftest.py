import pytest

from app.api.dependencies import get_company_resolver
from app.domain.models import Security
from app.main import app
from app.services.company_resolver import CompanyResolver


@pytest.fixture(autouse=True)
def override_company_resolver():
    resolver = CompanyResolver(
        [
            Security(
                company_name="Tata Motors Limited",
                symbol="TATAMOTORS",
                exchange="NSE",
                isin="INE155A01022",
            ),
            Security(
                company_name="Tata Motors Limited",
                symbol="TATAMOTORS",
                exchange="BSE",
                isin="INE155A01022",
            ),
        ]
    )

    app.dependency_overrides[get_company_resolver] = lambda: resolver

    yield

    app.dependency_overrides.clear()