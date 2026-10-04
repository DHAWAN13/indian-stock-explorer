from abc import ABC
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.domain.market_data import MarketQuote
from app.providers.market_data.base import (
    MarketDataProvider,
    MarketDataProviderError,
)


class FakeMarketDataProvider(MarketDataProvider):
    def get_quote(
        self,
        symbol: str,
        exchange: str,
    ) -> MarketQuote | None:
        if symbol == "UNKNOWN":
            return None

        if symbol == "FAIL":
            raise MarketDataProviderError("Provider unavailable.")

        return MarketQuote(
            symbol=symbol,
            exchange=exchange,
            price=Decimal("750.00"),
            previous_close=Decimal("740.00"),
            currency="INR",
            timestamp=datetime.now(timezone.utc),
            source="test",
        )


def test_market_data_provider_is_an_interface():
    assert issubclass(MarketDataProvider, ABC)

    with pytest.raises(TypeError):
        MarketDataProvider()


def test_fake_provider_returns_quote():
    provider = FakeMarketDataProvider()

    quote = provider.get_quote("TMPV", "NSE")

    assert quote is not None
    assert quote.symbol == "TMPV"
    assert quote.exchange == "NSE"
    assert quote.price == Decimal("750.00")
    assert quote.change == Decimal("10.00")


def test_fake_provider_returns_none_when_quote_is_missing():
    provider = FakeMarketDataProvider()

    assert provider.get_quote("UNKNOWN", "NSE") is None


def test_fake_provider_raises_error_when_provider_fails():
    provider = FakeMarketDataProvider()

    with pytest.raises(
        MarketDataProviderError,
        match="Provider unavailable",
    ):
        provider.get_quote("FAIL", "NSE")
