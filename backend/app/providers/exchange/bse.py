import csv
from pathlib import Path

from app.domain.models import Security
from app.providers.exchange.base import ExchangeProvider


class BSEProvider(ExchangeProvider):
    def __init__(self, data_path: Path):
        self.data_path = data_path

    def get_securities(self) -> list[Security]:
        with self.data_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            securities = []

            for row in reader:
                if row["SctyTpFlg"].strip().upper() != "EQ":
                    continue

                if row["FinInstrmTp"].strip().upper() != "E":
                    continue

                if row["Sts"].strip().upper() != "A":
                    continue

                symbol = row["TckrSymb"].strip()

                if symbol.endswith("#"):
                    continue

                securities.append(
                    Security(
                        company_name=row["FinInstrmNm"].strip(),
                        symbol=symbol,
                        exchange="BSE",
                        isin=row["ISIN"].strip() or None,
                        security_code=row["FinInstrmId"].strip() or None,
                    )
                )

            return securities