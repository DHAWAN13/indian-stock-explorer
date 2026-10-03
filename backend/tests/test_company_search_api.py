from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_company_resolver
from app.domain.models import Security
from app.main import app
from app.services.company_resolver import CompanyResolver


FIXTURES = Path(__file__).parent / "fixtures"

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

client = TestClient(app)


def test_company_search_api():
    response = client.get(
        "/api/v1/companies/search",
        params={"q": "Tata Motors"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "Tata Motors"
    assert data["resolution_status"] == "RESOLVED"
    assert len(data["matches"]) == 2
    assert {item["exchange"] for item in data["matches"]} == {"NSE", "BSE"}


def test_company_search_requires_query():
    response = client.get("/api/v1/companies/search")

    assert response.status_code == 422