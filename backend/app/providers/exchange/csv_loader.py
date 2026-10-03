import csv
from pathlib import Path

from app.domain.models import Security


def load_securities(path: Path) -> list[Security]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        return [
            Security(
                company_name=row["company_name"].strip(),
                symbol=row["symbol"].strip(),
                exchange=row["exchange"].strip(),
                isin=row["isin"].strip() or None,
                security_code=row["security_code"].strip() or None,
            )
            for row in reader
        ]