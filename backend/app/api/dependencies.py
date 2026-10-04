import os
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException

from app.providers.exchange.bse import BSEProvider
from app.providers.exchange.file_provider import find_security_file
from app.providers.exchange.nse import NSEProvider
from app.services.company_resolver import CompanyResolver

from app.providers.market_data.base import MarketDataProvider
from app.providers.market_data.file_provider import FileMarketDataProvider
from app.providers.market_data.yahoo_finance import YahooFinanceProvider


@lru_cache
def get_company_resolver() -> CompanyResolver:
    data_dir = os.getenv("EXCHANGE_DATA_DIR")

    if not data_dir:
        raise HTTPException(
            status_code=503,
            detail="Exchange data is not configured.",
        )

    data_path = Path(data_dir)

    try:
        nse_file = find_security_file(data_path, "NSE")
        bse_file = find_security_file(data_path, "BSE")
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Exchange data is unavailable: {exc}",
        ) from exc

    return CompanyResolver.from_providers(
        [
            NSEProvider(nse_file),
            BSEProvider(bse_file),
        ]
    )


@lru_cache
def get_market_data_provider() -> MarketDataProvider:
    provider_name = os.getenv(
        "MARKET_DATA_PROVIDER", "yahoo"
    ).strip().lower()

    if provider_name == "yahoo":
        return YahooFinanceProvider()

    if provider_name == "file":
        data_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "sample_quotes.json"
        )
        return FileMarketDataProvider(data_path)

    raise HTTPException(
        status_code=503,
        detail="Unsupported MARKET_DATA_PROVIDER configuration.",
    )