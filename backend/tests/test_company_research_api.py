from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_company_resolver,
    get_market_data_provider,
)
from app.domain.market_data import MarketQuote
from app.domain.models import ResolutionStatus
from app.main import app
from app.providers.market_data.base import MarketDataProviderError

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_dependencies():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def make_security(symbol="TMPV", exchange="NSE"):
    return SimpleNamespace(
        company_name="Tata Motors Passenger Vehicles Limited",
        symbol=symbol,
        exchange=exchange,
        isin="INE123A01016",
        security_code=None,
    )


def make_quote(symbol="TMPV", exchange="NSE"):
    return MarketQuote(
        symbol=symbol,
        exchange=exchange,
        price=Decimal("750.00"),
        previous_close=Decimal("740.00"),
        currency="INR",
        timestamp=datetime(2026, 10, 4, 15, 30, tzinfo=timezone.utc),
        source="test",
    )


def configure_resolver(status, matches):
    result = SimpleNamespace(
        query="TMPV",
        status=status,
        matches=matches,
    )
    resolver = Mock()
    resolver.resolve.return_value = result
    app.dependency_overrides[get_company_resolver] = lambda: resolver
    return resolver


def test_research_returns_company_and_quotes():
    securities = [
        make_security("TMPV", "NSE"),
        make_security("TMPV", "BSE"),
    ]
    configure_resolver(ResolutionStatus.RESOLVED, securities)

    provider = Mock()
    provider.get_quote.side_effect = lambda symbol, exchange: (
        make_quote(symbol, exchange)
    )
    app.dependency_overrides[get_market_data_provider] = lambda: provider

    response = client.get(
        "/api/v1/companies/research",
        params={"q": "TMPV"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["company_name"] == securities[0].company_name
    assert len(body["listings"]) == 2
    assert body["listings"][0]["quote"]["price"] == "750.00"
    assert body["listings"][1]["quote"]["exchange"] == "BSE"


def test_research_returns_null_quote_when_quote_missing():
    configure_resolver(
        ResolutionStatus.RESOLVED,
        [make_security()],
    )

    provider = Mock()
    provider.get_quote.return_value = None
    app.dependency_overrides[get_market_data_provider] = lambda: provider

    response = client.get(
        "/api/v1/companies/research",
        params={"q": "TMPV"},
    )

    assert response.status_code == 200
    assert response.json()["listings"][0]["quote"] is None


def test_research_does_not_fetch_quotes_for_ambiguous_company():
    configure_resolver(
        ResolutionStatus.AMBIGUOUS,
        [
            make_security("TMCV", "NSE"),
            make_security("TMPV", "NSE"),
        ],
    )

    provider = Mock()
    app.dependency_overrides[get_market_data_provider] = lambda: provider

    response = client.get(
        "/api/v1/companies/research",
        params={"q": "Tata Motors"},
    )

    assert response.status_code == 200
    assert response.json()["company_name"] is None
    assert all(
        item["quote"] is None
        for item in response.json()["listings"]
    )
    provider.get_quote.assert_not_called()


def test_research_returns_503_when_provider_fails():
    configure_resolver(
        ResolutionStatus.RESOLVED,
        [make_security()],
    )

    provider = Mock()
    provider.get_quote.side_effect = MarketDataProviderError(
        "Provider unavailable."
    )
    app.dependency_overrides[get_market_data_provider] = lambda: provider

    response = client.get(
        "/api/v1/companies/research",
        params={"q": "TMPV"},
    )

    assert response.status_code == 503