import os
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException

from app.providers.exchange.bse import BSEProvider
from app.providers.exchange.nse import NSEProvider
from app.services.company_resolver import CompanyResolver


@lru_cache
def get_company_resolver() -> CompanyResolver:
    data_dir = os.getenv("EXCHANGE_DATA_DIR")

    if not data_dir:
        raise HTTPException(
            status_code=503,
            detail="Exchange data is not configured.",
        )

    data_path = Path(data_dir)

    return CompanyResolver.from_providers(
        [
            NSEProvider(data_path / "nse_securities.csv"),
            BSEProvider(data_path / "bse_securities.csv"),
        ]
    )