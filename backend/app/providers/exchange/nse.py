import csv
import gzip
from pathlib import Path

from app.domain.models import Security
from app.providers.exchange.base import ExchangeProvider


class NSEProvider(ExchangeProvider):
    def __init__(self, data_path: Path):
        self.data_path = data_path

    def get_securities(self) -> list[Security]:
        with gzip.open(
            self.data_path,
            "rt",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            securities = []

            for row in reader:
                if row["SctySrs"].strip().upper() != "EQ":
                    continue

                if row.get("DelFlg", "").strip().upper() == "Y":
                    continue

                securities.append(
                    Security(
                        company_name=row["FinInstrmNm"].strip(),
                        symbol=row["TckrSymb"].strip(),
                        exchange="NSE",
                        isin=row["ISIN"].strip() or None,
                        security_code=row["FinInstrmId"].strip() or None,
                    )
                )

            return securities