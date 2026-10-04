from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_market_data_provider
from app.domain.market_data import HistoricalPriceBar
from app.main import app
from app.providers.market_data.base import MarketDataProviderError


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_dependencies():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def make_bar():
    return HistoricalPriceBar(
        timestamp=datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc),
        open=Decimal("740.00"),
        high=Decimal("755.00"),
        low=Decimal("738.00"),
        close=Decimal("750.00"),
        volume=120000,
    )


def test_history_endpoint_returns_real_provider_bars():
    provider = Mock()
    provider.get_history.return_value = [make_bar()]
    app.dependency_overrides[get_market_data_provider] = lambda: provider

    response = client.get(
        "/api/v1/companies/history",
        params={"symbol": "TMPV", "exchange": "NSE", "range": "1M"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "TMPV"
    assert body["exchange"] == "NSE"
    assert body["range"] == "1M"
    assert body["bars"][0]["close"] == "750.00"
    assert body["bars"][0]["volume"] == 120000
    provider.get_history.assert_called_once_with("TMPV", "NSE", "1M")


def test_history_endpoint_returns_empty_bars_when_no_data():
    provider = Mock()
    provider.get_history.return_value = []
    app.dependency_overrides[get_market_data_provider] = lambda: provider

    response = client.get(
        "/api/v1/companies/history",
        params={"symbol": "UNKNOWN", "exchange": "NSE", "range": "1M"},
    )

    assert response.status_code == 200
    assert response.json()["bars"] == []


def test_history_endpoint_returns_503_when_provider_fails():
    provider = Mock()
    provider.get_history.side_effect = MarketDataProviderError("Unavailable")
    app.dependency_overrides[get_market_data_provider] = lambda: provider

    response = client.get(
        "/api/v1/companies/history",
        params={"symbol": "TMPV", "exchange": "NSE", "range": "1M"},
    )

    assert response.status_code == 503


def test_history_endpoint_rejects_invalid_range():
    response = client.get(
        "/api/v1/companies/history",
        params={"symbol": "TMPV", "exchange": "NSE", "range": "10Y"},
    )

    assert response.status_code == 422