from pathlib import Path

from app.domain.models import Security
from app.providers.exchange.base import ExchangeProvider
from app.providers.exchange.csv_loader import load_securities


class BSEProvider(ExchangeProvider):
    def __init__(self, data_path: Path):
        self.data_path = data_path

    def get_securities(self) -> list[Security]:
        return load_securities(self.data_path)