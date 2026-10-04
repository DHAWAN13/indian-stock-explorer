from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_overview_returns_company_and_listings():
    response = client.get(
        "/api/v1/companies/overview",
        params={"q": "Tata Motors"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["resolution_status"] == "RESOLVED"
    assert data["listing_status"] == "LISTED"
    assert data["company_name"] == "Tata Motors Limited"
    assert len(data["listings"]) == 2
    assert {
        listing["exchange"] for listing in data["listings"]
    } == {"NSE", "BSE"}


def test_overview_returns_not_found():
    response = client.get(
        "/api/v1/companies/overview",
        params={"q": "Unknown Company"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["resolution_status"] == "NOT_FOUND"
    assert data["listing_status"] == "NOT_LISTED"
    assert data["company_name"] is None
    assert data["listings"] == []


def test_overview_requires_query():
    response = client.get("/api/v1/companies/overview")

    assert response.status_code == 422