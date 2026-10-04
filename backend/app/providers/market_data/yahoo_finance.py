import time
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
    """Fetch daily quotes with bounded retries and request timeouts."""

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

        base_symbol = clean_symbol.removesuffix(".NS").removesuffix(".BO")
        yahoo_symbol = (
            f"{base_symbol}.NS"
            if clean_exchange == "NSE"
            else f"{base_symbol}.BO"
        )

        history = None

        for attempt in range(1, self._max_attempts + 1):
            try:
                history = self._ticker_factory(yahoo_symbol).history(
                    period="5d",
                    interval="1d",
                    auto_adjust=False,
                    raise_errors=True,
                    timeout=self._timeout_seconds,
                )
                break
            except Exception as exc:
                if attempt == self._max_attempts:
                    raise MarketDataProviderError(
                        f"Yahoo Finance request failed for {yahoo_symbol} "
                        f"after {attempt} attempts."
                    ) from exc

                delay = self._retry_delay_seconds * (2 ** (attempt - 1))
                self._sleeper(delay)

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

            if (
                not price.is_finite()
                or not previous_close.is_finite()
                or price <= 0
                or previous_close <= 0
            ):
                raise ValueError("Prices must be positive and finite.")

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
        except (
            InvalidOperation,
            ValueError,
            TypeError,
            ArithmeticError,
        ) as exc:
            raise MarketDataProviderError(
                f"Invalid Yahoo Finance quote for {yahoo_symbol}."
            ) from exc