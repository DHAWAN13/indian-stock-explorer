from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class MarketQuote:
    symbol: str
    exchange: str
    price: Decimal
    previous_close: Decimal
    currency: str
    timestamp: datetime
    source: str

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("Symbol cannot be empty.")
        if not self.exchange.strip():
            raise ValueError("Exchange cannot be empty.")
        if (
            not self.price.is_finite()
            or self.price <= Decimal("0")
        ):
            raise ValueError("Price must be positive and finite.")
        if (
            not self.previous_close.is_finite()
            or self.previous_close <= Decimal("0")
        ):
            raise ValueError("Previous close must be positive and finite.")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("Timestamp must include a timezone.")

    @property
    def change(self) -> Decimal:
        return self.price - self.previous_close

    @property
    def change_percent(self) -> Decimal:
        return (
            self.change / self.previous_close * Decimal("100")
        ).quantize(Decimal("0.01"))


@dataclass(frozen=True)
class HistoricalPriceBar:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int | None

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("Timestamp must include a timezone.")

        prices = (self.open, self.high, self.low, self.close)

        if any(not price.is_finite() or price <= 0 for price in prices):
            raise ValueError("OHLC prices must be positive and finite.")

        if self.high < max(self.open, self.low, self.close):
            raise ValueError("High cannot be below another OHLC price.")

        if self.low > min(self.open, self.high, self.close):
            raise ValueError("Low cannot be above another OHLC price.")

        if self.volume is not None and self.volume < 0:
            raise ValueError("Volume cannot be negative.")