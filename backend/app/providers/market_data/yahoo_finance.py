import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

from app.domain.market_data import HistoricalPriceBar, MarketQuote
from app.providers.market_data.base import (
    MarketDataProvider,
    MarketDataProviderError,
)


INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")


HISTORY_RANGES = {
    # Fetch a wider window because Yahoo may return no data for period="1d".
    # get_history() filters this to the latest available trading session.
    "1D": ("5d", "5m"),
    "5D": ("5d", "15m"),
    "1M": ("1mo", "1d"),
    "6M": ("6mo", "1d"),
    "YTD": ("ytd", "1d"),
    "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"),
    "MAX": ("max", "1mo"),
}


class YahooFinanceProvider(MarketDataProvider):
    """Fetch quotes and historical OHLCV bars with bounded retries."""

    def __init__(
        self,
        ticker_factory: Callable[[str], Any] | None = None,
        timeout_seconds: float = 10.0,
        max_attempts: int = 3,
        retry_delay_seconds: float = 0.5,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Timeout must be positive.")
        if max_attempts < 1:
            raise ValueError("At least one attempt is required.")
        if retry_delay_seconds < 0:
            raise ValueError("Retry delay cannot be negative.")

        self._ticker_factory = ticker_factory or yf.Ticker
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._retry_delay_seconds = retry_delay_seconds
        self._sleeper = sleeper

    @staticmethod
    def _normalize_symbol(
        symbol: str,
        exchange: str,
    ) -> tuple[str, str, str]:
        clean_symbol = symbol.strip().upper()
        clean_exchange = exchange.strip().upper()

        if not clean_symbol or clean_exchange not in {"NSE", "BSE"}:
            raise MarketDataProviderError(
                "A valid symbol and NSE/BSE exchange are required."
            )

        base_symbol = clean_symbol.removesuffix(".NS").removesuffix(".BO")
        suffix = ".NS" if clean_exchange == "NSE" else ".BO"

        return base_symbol, clean_exchange, f"{base_symbol}{suffix}"

    def _fetch_history(
        self,
        yahoo_symbol: str,
        period: str,
        interval: str,
    ) -> Any:
        for attempt in range(1, self._max_attempts + 1):
            try:
                return self._ticker_factory(yahoo_symbol).history(
                    period=period,
                    interval=interval,
                    auto_adjust=False,
                    raise_errors=True,
                    timeout=self._timeout_seconds,
                )
            except Exception as exc:
                if attempt == self._max_attempts:
                    raise MarketDataProviderError(
                        f"Yahoo Finance request failed for {yahoo_symbol} "
                        f"after {attempt} attempts."
                    ) from exc

                delay = self._retry_delay_seconds * (2 ** (attempt - 1))
                self._sleeper(delay)

        raise MarketDataProviderError("Yahoo Finance request failed.")

    @staticmethod
    def _normalize_timestamp(value: Any) -> datetime:
        if hasattr(value, "to_pydatetime"):
            value = value.to_pydatetime()

        if not isinstance(value, datetime):
            raise ValueError("Invalid quote timestamp.")

        if value.tzinfo is None or value.utcoffset() is None:
            value = value.replace(tzinfo=timezone.utc)

        return value

    @staticmethod
    def _market_session_date(value: Any):
        """Return the timestamp's Indian market date."""
        if hasattr(value, "to_pydatetime"):
            value = value.to_pydatetime()

        if not isinstance(value, datetime):
            raise ValueError("Invalid historical data timestamp.")

        # Naive timestamps are treated as exchange-local timestamps.
        # Timezone-aware timestamps are converted to Indian Standard Time.
        if value.tzinfo is None or value.utcoffset() is None:
            return value.date()

        return value.astimezone(INDIA_TIMEZONE).date()

    def get_quote(
        self,
        symbol: str,
        exchange: str,
    ) -> MarketQuote | None:
        base_symbol, clean_exchange, yahoo_symbol = self._normalize_symbol(
            symbol, exchange
        )

        history = self._fetch_history(yahoo_symbol, "5d", "1d")

        if history is None or history.empty:
            return None

        if "Close" not in history.columns:
            raise MarketDataProviderError(
                "Yahoo Finance response has no closing-price data."
            )

        closes = history["Close"].dropna()

        if len(closes) < 2:
            return None

        try:
            price = Decimal(str(closes.iloc[-1]))
            previous_close = Decimal(str(closes.iloc[-2]))
            timestamp = self._normalize_timestamp(closes.index[-1])

            return MarketQuote(
                symbol=base_symbol,
                exchange=clean_exchange,
                price=price,
                previous_close=previous_close,
                currency="INR",
                timestamp=timestamp,
                source="Yahoo Finance via yfinance",
            )
        except (
            InvalidOperation,
            ValueError,
            TypeError,
            ArithmeticError,
        ) as exc:
            raise MarketDataProviderError(
                f"Invalid Yahoo Finance quote for {yahoo_symbol}."
            ) from exc

    def get_history(
        self,
        symbol: str,
        exchange: str,
        time_range: str,
    ) -> list[HistoricalPriceBar]:
        base_symbol, _, yahoo_symbol = self._normalize_symbol(
            symbol, exchange
        )

        normalized_range = time_range.strip().upper()

        if normalized_range not in HISTORY_RANGES:
            raise MarketDataProviderError(
                "Unsupported history range. Use 1D, 5D, 1M, 6M, YTD, 1Y, 5Y, or MAX."
            )

        period, interval = HISTORY_RANGES[normalized_range]
        history = self._fetch_history(yahoo_symbol, period, interval)

        if history is None or history.empty:
            return []

        # Use the latest available trading session for the 1D chart.
        if normalized_range == "1D":
            try:
                latest_session = self._market_session_date(
                    history.index[-1]
                )
                session_mask = [
                    self._market_session_date(timestamp) == latest_session
                    for timestamp in history.index
                ]
                history = history.loc[session_mask]
            except (TypeError, ValueError, OverflowError) as exc:
                raise MarketDataProviderError(
                    f"Invalid historical timestamps for {base_symbol}."
                ) from exc

        if history.empty:
            return []

        required_columns = ("Open", "High", "Low", "Close")
        missing = [
            column
            for column in required_columns
            if column not in history.columns
        ]

        if missing:
            raise MarketDataProviderError(
                "Yahoo Finance response is missing columns: "
                f"{', '.join(missing)}."
            )

        bars = []

        for timestamp, row in history.iterrows():
            if any(
                pd.isna(row[column])
                for column in required_columns
            ):
                continue

            try:
                open_price = Decimal(str(row["Open"]))
                high_price = Decimal(str(row["High"]))
                low_price = Decimal(str(row["Low"]))
                close_price = Decimal(str(row["Close"]))

                prices = (
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                )

                # Reject non-finite or non-positive prices.
                if not all(
                    price.is_finite() and price > 0
                    for price in prices
                ):
                    continue

                # Reject inconsistent OHLC candles individually. Do not
                # discard the entire historical response for one bad bar.
                if (
                    low_price > min(open_price, close_price)
                    or high_price < max(open_price, close_price)
                    or low_price > high_price
                ):
                    continue

                raw_volume = row.get("Volume")
                volume = (
                    None
                    if raw_volume is None or pd.isna(raw_volume)
                    else int(raw_volume)
                )

                bars.append(
                    HistoricalPriceBar(
                        timestamp=self._normalize_timestamp(timestamp),
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=volume,
                    )
                )

            except (
                InvalidOperation,
                ValueError,
                TypeError,
                ArithmeticError,
            ) as exc:
                raise MarketDataProviderError(
                    f"Invalid historical data for {base_symbol}."
                ) from exc

        return bars