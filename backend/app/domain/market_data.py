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

        if self.price <= Decimal("0"):
            raise ValueError("Price must be positive.")

        if self.previous_close <= Decimal("0"):
            raise ValueError("Previous close must be positive.")

        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("Timestamp must include a timezone.")

    @property
    def change(self) -> Decimal:
        return self.price - self.previous_close

    @property
    def change_percent(self) -> Decimal:
        percentage = self.change / self.previous_close * Decimal("100")
        return percentage.quantize(Decimal("0.01"))