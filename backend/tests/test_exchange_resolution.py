import csv
import gzip
import io
from pathlib import Path

from app.domain.models import ResolutionStatus
from app.providers.exchange.bse import BSEProvider
from app.providers.exchange.nse import NSEProvider
from app.services.company_resolver import CompanyResolver


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

    with gzip.open(
        path,
        "wt",
        encoding="utf-8",
        newline="",
    ) as file:
        file.write(output.getvalue())


def create_bse_fixture(path: Path) -> None:
    path.write_text(
        "FinInstrmId,TckrSymb,FinInstrmNm,ISIN,SctyTpFlg,FinInstrmTp,Sts\n"
        "500570,TMPV,TATA MOTORS PASSENGER VEHICLES,"
        "INE155A01022,EQ,E,A\n",
        encoding="utf-8",
    )


def test_resolves_company_across_nse_and_bse(tmp_path: Path):
    nse_path = tmp_path / "NSE_CM_security_01102026.csv.gz"
    bse_path = tmp_path / "BSE_EQ_SCRIP_01102026.csv"

    create_nse_fixture(nse_path)
    create_bse_fixture(bse_path)

    resolver = CompanyResolver.from_providers(
        [
            NSEProvider(nse_path),
            BSEProvider(bse_path),
        ]
    )

    result = resolver.resolve("TATA MOTORS PASS VEH LTD")

    assert result.status == ResolutionStatus.RESOLVED
    assert len(result.matches) == 2
    assert {match.exchange for match in result.matches} == {"NSE", "BSE"}


def test_symbol_resolution_returns_matching_security(tmp_path: Path):
    nse_path = tmp_path / "NSE_CM_security_01102026.csv.gz"
    bse_path = tmp_path / "BSE_EQ_SCRIP_01102026.csv"

    create_nse_fixture(nse_path)
    create_bse_fixture(bse_path)

    resolver = CompanyResolver.from_providers(
        [
            NSEProvider(nse_path),
            BSEProvider(bse_path),
        ]
    )

    result = resolver.resolve("TMPV")

    assert result.status == ResolutionStatus.RESOLVED
    assert len(result.matches) == 2