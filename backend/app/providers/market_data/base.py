from abc import ABC, abstractmethod

from app.domain.market_data import MarketQuote, HistoricalPriceBar


class MarketDataProviderError(Exception):
    """Raised when a market-data provider cannot supply a reliable response."""


class MarketDataProvider(ABC):
    """Interface for retrieving market quotes and historical prices."""

    @abstractmethod
    def get_quote(
        self,
        symbol: str,
        exchange: str,
    ) -> MarketQuote | None:
        """Return a quote, or None when unavailable."""
        raise NotImplementedError

    def get_history(
        self,
        symbol: str,
        exchange: str,
        time_range: str,
    ) -> list[HistoricalPriceBar]:
        """Return historical OHLCV bars when supported by the provider."""
        raise MarketDataProviderError(
            "Historical price data is not supported by this provider."
        )