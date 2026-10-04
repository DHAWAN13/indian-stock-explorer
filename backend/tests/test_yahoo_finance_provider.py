from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pandas as pd
import pytest

from app.providers.market_data.base import MarketDataProviderError
from app.providers.market_data.yahoo_finance import YahooFinanceProvider


def make_history():
    index = pd.DatetimeIndex(
        [
            datetime(2026, 10, 2, 10, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc),
        ]
    )
    return pd.DataFrame({"Close": [740.0, 750.0]}, index=index)


def test_nse_quote_is_normalized_and_returned():
    ticker = Mock()
    ticker.history.return_value = make_history()
    factory = Mock(return_value=ticker)

    provider = YahooFinanceProvider(ticker_factory=factory)
    quote = provider.get_quote("TMPV", "NSE")

    factory.assert_called_once_with("TMPV.NS")
    assert quote is not None
    assert quote.symbol == "TMPV"
    assert quote.exchange == "NSE"
    assert quote.price == Decimal("750.0")
    assert quote.previous_close == Decimal("740.0")
    assert quote.change == Decimal("10.0")
    assert quote.currency == "INR"


def test_bse_quote_uses_bo_suffix():
    ticker = Mock()
    ticker.history.return_value = make_history()
    factory = Mock(return_value=ticker)

    quote = YahooFinanceProvider(
        ticker_factory=factory
    ).get_quote("TMPV", "BSE")

    factory.assert_called_once_with("TMPV.BO")
    assert quote is not None
    assert quote.exchange == "BSE"


def test_empty_history_returns_none():
    ticker = Mock()
    ticker.history.return_value = pd.DataFrame(
        columns=["Close"]
    )

    provider = YahooFinanceProvider(
        ticker_factory=Mock(return_value=ticker)
    )

    assert provider.get_quote("UNKNOWN", "NSE") is None


def test_yahoo_failure_raises_provider_error():
    ticker = Mock()
    ticker.history.side_effect = RuntimeError("Network error")

    provider = YahooFinanceProvider(
        ticker_factory=Mock(return_value=ticker)
    )

    with pytest.raises(MarketDataProviderError):
        provider.get_quote("TMPV", "NSE")


def test_invalid_exchange_is_rejected():
    provider = YahooFinanceProvider(ticker_factory=Mock())

    with pytest.raises(MarketDataProviderError):
        provider.get_quote("TMPV", "NYSE")


def test_single_daily_observation_returns_none():
    ticker = Mock()
    ticker.history.return_value = make_history().iloc[:1]

    provider = YahooFinanceProvider(
        ticker_factory=Mock(return_value=ticker)
    )

    assert provider.get_quote("TMPV", "NSE") is None