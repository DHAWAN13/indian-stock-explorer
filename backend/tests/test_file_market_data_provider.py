
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.providers.market_data.base import MarketDataProviderError
from app.providers.market_data.file_provider import FileMarketDataProvider


def create_quotes_file(path: Path, records: list) -> None:
    path.write_text(json.dumps(records), encoding="utf-8")


def sample_quote() -> dict:
    return {
        "symbol": "TMPV",
        "exchange": "NSE",
        "price": "750.00",
        "previous_close": "740.00",
        "currency": "INR",
        "timestamp": "2026-10-04T15:30:00+05:30",
        "source": "sample",
    }


def test_returns_matching_quote(tmp_path: Path):
    path = tmp_path / "quotes.json"
    create_quotes_file(path, [sample_quote()])

    quote = FileMarketDataProvider(path).get_quote("tmpv", "nse")

    assert quote is not None
    assert quote.symbol == "TMPV"
    assert quote.exchange == "NSE"
    assert quote.price == Decimal("750.00")
    assert quote.change == Decimal("10.00")
    assert quote.change_percent == Decimal("1.35")
    assert quote.timestamp == datetime.fromisoformat(
        "2026-10-04T15:30:00+05:30"
    )


def test_returns_none_for_missing_quote(tmp_path: Path):
    path = tmp_path / "quotes.json"
    create_quotes_file(path, [sample_quote()])

    quote = FileMarketDataProvider(path).get_quote("RELIANCE", "NSE")

    assert quote is None


def test_rejects_invalid_matching_quote(tmp_path: Path):
    path = tmp_path / "quotes.json"
    record = sample_quote()
    record["price"] = "-1"
    create_quotes_file(path, [record])

    with pytest.raises(MarketDataProviderError, match="Invalid quote"):
        FileMarketDataProvider(path).get_quote("TMPV", "NSE")


def test_missing_file_raises_provider_error(tmp_path: Path):
    provider = FileMarketDataProvider(tmp_path / "missing.json")

    with pytest.raises(MarketDataProviderError, match="Could not load"):
        provider.get_quote("TMPV", "NSE")


def test_malformed_json_raises_provider_error(tmp_path: Path):
    path = tmp_path / "quotes.json"
    path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(MarketDataProviderError, match="Could not load"):
        FileMarketDataProvider(path).get_quote("TMPV", "NSE")