from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.domain.market_data import MarketQuote


def make_quote(
    price: str = "1000.50",
    previous_close: str = "990.00",
    timestamp: datetime | None = None,
) -> MarketQuote:
    return MarketQuote(
        symbol="TMPV",
        exchange="NSE",
        price=Decimal(price),
        previous_close=Decimal(previous_close),
        currency="INR",
        timestamp=timestamp or datetime(
            2026, 10, 4, 10, 0, tzinfo=timezone.utc
        ),
        source="test-provider",
    )


def test_calculates_positive_change():
    quote = make_quote()

    assert quote.change == Decimal("10.50")
    assert quote.change_percent == Decimal("1.06")


def test_calculates_negative_change():
    quote = make_quote(price="980.00", previous_close="1000.00")

    assert quote.change == Decimal("-20.00")
    assert quote.change_percent == Decimal("-2.00")


def test_rejects_zero_previous_close():
    with pytest.raises(ValueError, match="Previous close must be positive"):
        make_quote(previous_close="0")


def test_rejects_timezone_naive_timestamp():
    with pytest.raises(ValueError, match="Timestamp must include a timezone"):
        make_quote(timestamp=datetime(2026, 10, 4, 10, 0))