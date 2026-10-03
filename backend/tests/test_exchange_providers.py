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
        }
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

    with gzip.open(path, "wt", encoding="utf-8", newline="") as file:
        file.write(output.getvalue())


def create_bse_fixture(path: Path) -> None:
    path.write_text(
        "FinInstrmId,TckrSymb,FinInstrmNm,ISIN,SctyTpFlg,FinInstrmTp,Sts\n"
        "500570,TMPV,TATA MOTORS PASSENGER VEHICLES,INE155A01022,EQ,E,A\n",
        encoding="utf-8",
    )


def test_nse_provider_filters_to_eq_series(tmp_path: Path):
    path = tmp_path / "NSE_CM_security_01102026.csv.gz"
    create_nse_fixture(path)

    securities = NSEProvider(path).get_securities()

    assert len(securities) == 1
    assert securities[0].symbol == "TMPV"
    assert securities[0].exchange == "NSE"


def test_bse_provider_filters_active_equity(tmp_path: Path):
    path = tmp_path / "BSE_EQ_SCRIP_01102026.csv"
    create_bse_fixture(path)

    securities = BSEProvider(path).get_securities()

    assert len(securities) == 1
    assert securities[0].symbol == "TMPV"
    assert securities[0].exchange == "BSE"
    assert securities[0].security_code == "500570"