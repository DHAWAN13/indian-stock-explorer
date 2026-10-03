from app.domain.models import ResolutionStatus, Security
from app.services.company_resolver import CompanyResolver


SECURITIES = [
    Security(
        company_name="Tata Motors Limited",
        symbol="TATAMOTORS",
        exchange="NSE",
        isin="INE155A01022",
    ),
    Security(
        company_name="Infosys Limited",
        symbol="INFY",
        exchange="NSE",
    ),
]


def test_resolves_company_name():
    resolver = CompanyResolver(SECURITIES)

    result = resolver.resolve("Tata Motors")

    assert result.status == ResolutionStatus.RESOLVED
    assert result.matches[0].symbol == "TATAMOTORS"


def test_resolves_symbol():
    resolver = CompanyResolver(SECURITIES)

    result = resolver.resolve("INFY")

    assert result.status == ResolutionStatus.RESOLVED


def test_returns_not_found():
    resolver = CompanyResolver(SECURITIES)

    result = resolver.resolve("Unknown Company")

    assert result.status == ResolutionStatus.NOT_FOUND