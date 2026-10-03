from pathlib import Path

from app.providers.exchange.bse import BSEProvider
from app.providers.exchange.nse import NSEProvider


FIXTURES = Path(__file__).parent / "fixtures"


def test_nse_provider_loads_securities():
    provider = NSEProvider(FIXTURES / "nse_securities.csv")

    securities = provider.get_securities()

    assert len(securities) == 2
    assert securities[0].symbol == "TATAMOTORS"
    assert securities[0].exchange == "NSE"


def test_bse_provider_loads_securities():
    provider = BSEProvider(FIXTURES / "bse_securities.csv")

    securities = provider.get_securities()

    assert len(securities) == 2
    assert securities[0].isin == "INE155A01022"
    assert securities[0].exchange == "BSE"