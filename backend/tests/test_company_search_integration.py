from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_company_search_uses_exchange_providers():
    response = client.get(
        "/api/v1/companies/search",
        params={"q": "Tata Motors"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["resolution_status"] == "RESOLVED"
    assert len(data["matches"]) == 2
    assert {item["exchange"] for item in data["matches"]} == {"NSE", "BSE"}