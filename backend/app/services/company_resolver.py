import re
from collections.abc import Iterable

from app.domain.models import ResolutionResult, ResolutionStatus, Security
from app.providers.exchange.base import ExchangeProvider


class CompanyResolver:
    def __init__(self, securities: list[Security]):
        self.securities = securities

    @classmethod
    def from_providers(
        cls,
        providers: Iterable[ExchangeProvider],
    ) -> "CompanyResolver":
        securities: list[Security] = []

        for provider in providers:
            securities.extend(provider.get_securities())

        return cls(securities)

    def resolve(self, query: str) -> ResolutionResult:
        normalized = self._normalize(query)

        if not normalized:
            return ResolutionResult(
                query=query,
                status=ResolutionStatus.NOT_FOUND,
                matches=[],
            )

        matches = [
            security
            for security in self.securities
            if normalized in {
                self._normalize(security.company_name),
                self._normalize(security.symbol),
            }
        ]

        if not matches:
            status = ResolutionStatus.NOT_FOUND
        elif self._is_single_company(matches):
            status = ResolutionStatus.RESOLVED
        else:
            status = ResolutionStatus.AMBIGUOUS

        return ResolutionResult(
            query=query,
            status=status,
            matches=matches,
        )

    @staticmethod
    def _is_single_company(matches: list[Security]) -> bool:
        identities = {
            security.isin or CompanyResolver._normalize(security.company_name)
            for security in matches
        }

        return len(identities) == 1

    @staticmethod
    def _normalize(value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"\b(limited|ltd)\b", "", value)
        value = re.sub(r"[^a-z0-9]+", " ", value)
        return " ".join(value.split())