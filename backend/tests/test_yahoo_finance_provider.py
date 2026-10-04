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

    ticker.history.assert_called_once_with(
        period="5d",
        interval="1d",
        auto_adjust=False,
        raise_errors=True,
        timeout=10.0,
    )


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
    ticker.history.return_value = pd.DataFrame(columns=["Close"])

    provider = YahooFinanceProvider(
        ticker_factory=Mock(return_value=ticker)
    )

    assert provider.get_quote("UNKNOWN", "NSE") is None


def test_yahoo_failure_raises_provider_error_after_retries():
    ticker = Mock()
    ticker.history.side_effect = RuntimeError("Network error")
    factory = Mock(return_value=ticker)
    sleeper = Mock()

    provider = YahooFinanceProvider(
        ticker_factory=factory,
        max_attempts=3,
        retry_delay_seconds=0.5,
        sleeper=sleeper,
    )

    with pytest.raises(MarketDataProviderError, match="3 attempts"):
        provider.get_quote("TMPV", "NSE")

    assert ticker.history.call_count == 3
    assert sleeper.call_args_list == [
        ((0.5,),),
        ((1.0,),),
    ]


def test_transient_failure_is_retried_successfully():
    ticker = Mock()
    ticker.history.side_effect = [
        RuntimeError("Temporary network error"),
        make_history(),
    ]
    sleeper = Mock()

    provider = YahooFinanceProvider(
        ticker_factory=Mock(return_value=ticker),
        sleeper=sleeper,
    )

    quote = provider.get_quote("TMPV", "NSE")

    assert quote is not None
    assert quote.price == Decimal("750.0")
    assert ticker.history.call_count == 2
    sleeper.assert_called_once_with(0.5)


def test_invalid_exchange_is_rejected_without_request():
    factory = Mock()
    provider = YahooFinanceProvider(ticker_factory=factory)

    with pytest.raises(MarketDataProviderError):
        provider.get_quote("TMPV", "NYSE")

    factory.assert_not_called()


def test_single_daily_observation_returns_none():
    ticker = Mock()
    ticker.history.return_value = make_history().iloc[:1]

    provider = YahooFinanceProvider(
        ticker_factory=Mock(return_value=ticker)
    )

    assert provider.get_quote("TMPV", "NSE") is None


def test_missing_close_column_raises_provider_error():
    ticker = Mock()
    ticker.history.return_value = pd.DataFrame({"Open": [740.0, 750.0]})

    provider = YahooFinanceProvider(
        ticker_factory=Mock(return_value=ticker)
    )

    with pytest.raises(
        MarketDataProviderError,
        match="no closing-price data",
    ):
        provider.get_quote("TMPV", "NSE")


def test_invalid_configuration_is_rejected():
    with pytest.raises(ValueError):
        YahooFinanceProvider(timeout_seconds=0)

    with pytest.raises(ValueError):
        YahooFinanceProvider(max_attempts=0)

def make_ohlcv_history():
    index = pd.DatetimeIndex(
        [
            datetime(2026, 10, 2, 10, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc),
        ]
    )

    return pd.DataFrame(
        {
            "Open": [735.0, 742.0],
            "High": [745.0, 755.0],
            "Low": [730.0, 738.0],
            "Close": [740.0, 750.0],
            "Volume": [100000, 120000],
        },
        index=index,
    )


def test_history_returns_real_ohlcv_bars_from_provider():
    ticker = Mock()
    ticker.history.return_value = make_ohlcv_history()

    provider = YahooFinanceProvider(
        ticker_factory=Mock(return_value=ticker),
    )

    bars = provider.get_history("TMPV", "NSE", "1M")

    assert len(bars) == 2
    assert bars[0].close == Decimal("740.0")
    assert bars[1].close == Decimal("750.0")
    assert bars[1].high == Decimal("755.0")
    assert bars[1].low == Decimal("738.0")
    assert bars[1].volume == 120000

    ticker.history.assert_called_once_with(
        period="1mo",
        interval="1d",
        auto_adjust=False,
        raise_errors=True,
        timeout=10.0,
    )


def test_history_uses_intraday_interval_for_one_day():
    ticker = Mock()
    ticker.history.return_value = make_ohlcv_history()

    provider = YahooFinanceProvider(
        ticker_factory=Mock(return_value=ticker),
    )

    provider.get_history("RELIANCE", "NSE", "1D")

    ticker.history.assert_called_once_with(
        period="5d",
        interval="5m",
        auto_adjust=False,
        raise_errors=True,
        timeout=10.0,
    )


def test_history_returns_empty_list_when_no_data():
    ticker = Mock()
    ticker.history.return_value = pd.DataFrame()

    provider = YahooFinanceProvider(
        ticker_factory=Mock(return_value=ticker),
    )

    assert provider.get_history("UNKNOWN", "NSE", "1M") == []


def test_history_rejects_unsupported_range():
    provider = YahooFinanceProvider(ticker_factory=Mock())

    with pytest.raises(MarketDataProviderError, match="Unsupported history range"):
        provider.get_history("TMPV", "NSE", "10Y")


def test_history_rejects_missing_ohlc_columns():
    ticker = Mock()
    ticker.history.return_value = pd.DataFrame({"Close": [740.0, 750.0]})

    provider = YahooFinanceProvider(
        ticker_factory=Mock(return_value=ticker),
    )

    with pytest.raises(MarketDataProviderError, match="missing columns"):
        provider.get_history("TMPV", "NSE", "1M")