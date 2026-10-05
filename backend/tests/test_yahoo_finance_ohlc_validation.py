from decimal import Decimal
from unittest.mock import Mock

import pandas as pd

from app.providers.market_data.yahoo_finance import YahooFinanceProvider


def test_history_skips_invalid_ohlc_candles_but_keeps_valid_candles():
    history = pd.DataFrame(
        {
            "Open": [100.0, 102.0, 101.0, 104.0],
            "High": [105.0, 101.0, 104.0, 103.0],
            "Low": [99.0, 99.0, 100.0, 104.5],
            "Close": [103.0, 100.5, 103.0, 103.5],
            "Volume": [1000, 2000, 3000, 4000],
        },
        index=pd.DatetimeIndex(
            [
                "1996-01-01 00:00:00+05:30",
                "1996-02-01 00:00:00+05:30",
                "1996-03-01 00:00:00+05:30",
                "1996-04-01 00:00:00+05:30",
            ]
        ),
    )

    ticker = Mock()
    ticker.history.return_value = history

    provider = YahooFinanceProvider(
        ticker_factory=Mock(return_value=ticker),
    )

    bars = provider.get_history("RELIANCE", "NSE", "MAX")

    # Keep the first and third candles; skip the second and fourth.
    assert len(bars) == 2
    assert [bar.close for bar in bars] == [
        Decimal("103.0"),
        Decimal("103.0"),
    ]

    assert [bar.timestamp for bar in bars] == [
        history.index[0].to_pydatetime(),
        history.index[2].to_pydatetime(),
    ]

    # The raw provider response must be requested with the MAX mapping.
    ticker.history.assert_called_once_with(
        period="max",
        interval="1mo",
        auto_adjust=False,
        raise_errors=True,
        timeout=10.0,
    )