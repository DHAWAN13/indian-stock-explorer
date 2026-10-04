from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

import yfinance as yf

from app.domain.market_data import MarketQuote
from app.providers.market_data.base import (
    MarketDataProvider,
    MarketDataProviderError,
)


class YahooFinanceProvider(MarketDataProvider):
    """Fetch daily market quotes through Yahoo Finance."""

    def __init__(
        self,
        ticker_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self._ticker_factory = ticker_factory or yf.Ticker

    def get_quote(
        self,
        symbol: str,
        exchange: str,
    ) -> MarketQuote | None:
        clean_symbol = symbol.strip().upper()
        clean_exchange = exchange.strip().upper()

        if not clean_symbol or clean_exchange not in {"NSE", "BSE"}:
            raise MarketDataProviderError(
                "A valid symbol and NSE/BSE exchange are required."
            )

        # Accept symbols with or without a Yahoo Finance suffix.
        base_symbol = clean_symbol.removesuffix(".NS").removesuffix(".BO")
        yahoo_symbol = (
            f"{base_symbol}.NS"
            if clean_exchange == "NSE"
            else f"{base_symbol}.BO"
        )

        try:
            history = self._ticker_factory(yahoo_symbol).history(
                period="5d",
                interval="1d",
                auto_adjust=False,
                raise_errors=True,
            )
        except Exception as exc:
            raise MarketDataProviderError(
                f"Yahoo Finance request failed for {yahoo_symbol}."
            ) from exc

        if history is None or history.empty:
            return None

        if "Close" not in history.columns:
            raise MarketDataProviderError(
                "Yahoo Finance response has no closing-price data."
            )

        closes = history["Close"].dropna()

        # Two observations are needed to calculate the daily change.
        if len(closes) < 2:
            return None

        try:
            price = Decimal(str(closes.iloc[-1]))
            previous_close = Decimal(str(closes.iloc[-2]))

            if not price.is_finite() or not previous_close.is_finite():
                raise ValueError("Prices must be finite numbers.")

            timestamp = history.index[-1]
            if hasattr(timestamp, "to_pydatetime"):
                timestamp = timestamp.to_pydatetime()

            if not isinstance(timestamp, datetime):
                raise ValueError("Invalid quote timestamp.")

            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            return MarketQuote(
                symbol=base_symbol,
                exchange=clean_exchange,
                price=price,
                previous_close=previous_close,
                currency="INR",
                timestamp=timestamp,
                source="Yahoo Finance via yfinance",
            )
        except (InvalidOperation, ValueError, TypeError, ArithmeticError) as exc:
            raise MarketDataProviderError(
                f"Invalid Yahoo Finance quote for {yahoo_symbol}."
            ) from exc