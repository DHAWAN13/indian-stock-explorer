from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_market_data_provider
from app.domain.market_data import MarketQuote
from app.main import app
from app.providers.market_data.base import MarketDataProviderError

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_dependencies():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def make_quote():
    return MarketQuote(
        symbol="TMPV",
        exchange="NSE",
        price=Decimal("750.00"),
        previous_close=Decimal("740.00"),
        currency="INR",
        timestamp=datetime(2026, 10, 4, 15, 30, tzinfo=timezone.utc),
        source="test",
    )


def test_quote_endpoint_returns_quote():
    provider = Mock()
    provider.get_quote.return_value = make_quote()
    app.dependency_overrides[get_market_data_provider] = lambda: provider

    response = client.get(
        "/api/v1/companies/quote",
        params={"symbol": "TMPV", "exchange": "NSE"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "TMPV"
    assert body["exchange"] == "NSE"
    assert body["price"] == "750.00"
    assert body["previous_close"] == "740.00"
    assert body["change"] == "10.00"
    assert body["currency"] == "INR"


def test_quote_endpoint_returns_404_when_quote_missing():
    provider = Mock()
    provider.get_quote.return_value = None
    app.dependency_overrides[get_market_data_provider] = lambda: provider

    response = client.get(
        "/api/v1/companies/quote",
        params={"symbol": "UNKNOWN", "exchange": "NSE"},
    )

    assert response.status_code == 404


def test_quote_endpoint_returns_503_when_provider_fails():
    provider = Mock()
    provider.get_quote.side_effect = MarketDataProviderError(
        "Provider unavailable."
    )
    app.dependency_overrides[get_market_data_provider] = lambda: provider

    response = client.get(
        "/api/v1/companies/quote",
        params={"symbol": "TMPV", "exchange": "NSE"},
    )

    assert response.status_code == 503


def test_quote_endpoint_rejects_invalid_exchange():
    response = client.get(
        "/api/v1/companies/quote",
        params={"symbol": "TMPV", "exchange": "NYSE"},
    )

    assert response.status_code == 422