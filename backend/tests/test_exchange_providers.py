import csv
import gzip
import io
from pathlib import Path

from app.providers.exchange.bse import BSEProvider
from app.providers.exchange.nse import NSEProvider


def create_nse_fixture(path: Path) -> None:
    rows = [
        {
            "FinInstrmId": "3456",
            "TckrSymb": "TMPV",
            "SctySrs": "EQ",
            "FinInstrmNm": "TATA MOTORS PASS VEH LTD",
            "ISIN": "INE155A01022",
            "DelFlg": "",
        },
        {
            "FinInstrmId": "9999",
            "TckrSymb": "TMPV",
            "SctySrs": "BE",
            "FinInstrmNm": "TATA MOTORS PASS VEH LTD",
            "ISIN": "INE155A01022",
            "DelFlg": "",
        },
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

    with gzip.open(path, "wt", encoding="utf-8", newline="") as file:
        file.write(output.getvalue())


def test_nse_provider_filters_to_eq_series(tmp_path: Path):
    path = tmp_path / "NSE_CM_security_01102026.csv.gz"
    create_nse_fixture(path)

    securities = NSEProvider(path).get_securities()

    assert len(securities) == 1
    assert securities[0].symbol == "TMPV"
    assert securities[0].company_name == "TATA MOTORS PASS VEH LTD"
    assert securities[0].isin == "INE155A01022"
    assert securities[0].security_code == "3456"
    assert securities[0].exchange == "NSE"


def test_bse_provider_still_loads():
    fixtures = Path(__file__).parent / "fixtures"

    securities = BSEProvider(
        fixtures / "bse_securities.csv"
    ).get_securities()

    assert len(securities) == 2
    assert securities[0].exchange == "BSE"