from abc import ABC, abstractmethod

from app.domain.market_data import MarketQuote


class MarketDataProviderError(Exception):
    """Raised when a market-data provider cannot supply a reliable response."""


class MarketDataProvider(ABC):
    """Interface for retrieving market quotes."""

    @abstractmethod
    def get_quote(
        self,
        symbol: str,
        exchange: str,
    ) -> MarketQuote | None:
        """Return a quote, or None when no quote is available.

        Raise MarketDataProviderError when the provider fails.
        """
        raise NotImplementedError
