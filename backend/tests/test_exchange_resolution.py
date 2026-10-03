from pathlib import Path

from app.domain.models import ResolutionStatus
from app.providers.exchange.bse import BSEProvider
from app.providers.exchange.nse import NSEProvider
from app.services.company_resolver import CompanyResolver


FIXTURES = Path(__file__).parent / "fixtures"


def test_resolves_company_across_nse_and_bse():
    resolver = CompanyResolver.from_providers(
        [
            NSEProvider(FIXTURES / "nse_securities.csv"),
            BSEProvider(FIXTURES / "bse_securities.csv"),
        ]
    )

    result = resolver.resolve("Tata Motors")

    assert result.status == ResolutionStatus.RESOLVED
    assert len(result.matches) == 2

    exchanges = {match.exchange for match in result.matches}

    assert exchanges == {"NSE", "BSE"}


def test_symbol_resolution_returns_matching_security():
    resolver = CompanyResolver.from_providers(
        [
            NSEProvider(FIXTURES / "nse_securities.csv"),
            BSEProvider(FIXTURES / "bse_securities.csv"),
        ]
    )

    result = resolver.resolve("INFY")

    assert result.status == ResolutionStatus.RESOLVED
    assert len(result.matches) == 2