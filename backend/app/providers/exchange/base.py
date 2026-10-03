from abc import ABC, abstractmethod

from app.domain.models import Security


class ExchangeProvider(ABC):
    @abstractmethod
    def get_securities(self) -> list[Security]:
        """Return normalized securities from the exchange."""
        raise NotImplementedError