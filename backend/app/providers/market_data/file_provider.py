
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.domain.market_data import MarketQuote
from app.providers.market_data.base import (
    MarketDataProvider,
    MarketDataProviderError,
)


class FileMarketDataProvider(MarketDataProvider):
    """Read explicitly supplied sample quotes from a JSON file."""

    def __init__(self, data_path: Path):
        self.data_path = data_path

    def get_quote(
        self,
        symbol: str,
        exchange: str,
    ) -> MarketQuote | None:
        try:
            with self.data_path.open("r", encoding="utf-8") as file:
                records = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            raise MarketDataProviderError(
                f"Could not load market data: {exc}"
            ) from exc

        if not isinstance(records, list):
            raise MarketDataProviderError(
                "Market data file must contain a JSON list."
            )

        for record in records:
            if not isinstance(record, dict):
                raise MarketDataProviderError(
                    "Market data records must be JSON objects."
                )

            if (
                str(record.get("symbol", "")).strip().upper()
                != symbol.strip().upper()
                or str(record.get("exchange", "")).strip().upper()
                != exchange.strip().upper()
            ):
                continue

            try:
                return MarketQuote(
                    symbol=record["symbol"],
                    exchange=record["exchange"],
                    price=Decimal(str(record["price"])),
                    previous_close=Decimal(
                        str(record["previous_close"])
                    ),
                    currency=record["currency"],
                    timestamp=datetime.fromisoformat(
                        record["timestamp"]
                    ),
                    source=record.get("source", "sample"),
                )
            except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
                raise MarketDataProviderError(
                    f"Invalid quote record for {symbol} on {exchange}."
                ) from exc

        return None
