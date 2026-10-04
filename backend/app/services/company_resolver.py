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

        # Exact ticker match takes priority.
        symbol_matches = [
            security
            for security in self.securities
            if self._normalize(security.symbol) == normalized
        ]

        if symbol_matches:
            direct_matches = symbol_matches
        else:
            # Allow partial company-name searches.
            direct_matches = [
                security
                for security in self.securities
                if normalized in self._normalize(security.company_name)
            ]

        if not direct_matches:
            return ResolutionResult(
                query=query,
                status=ResolutionStatus.NOT_FOUND,
                matches=[],
            )

        # Expand matches across exchanges using ISIN.
        matched_isins = {
            security.isin
            for security in direct_matches
            if security.isin
        }

        matches = list(direct_matches)

        for security in self.securities:
            if (
                security.isin
                and security.isin in matched_isins
                and security not in matches
            ):
                matches.append(security)

        # Multiple ISINs mean the query may refer to different companies.
        status = (
            ResolutionStatus.RESOLVED
            if self._is_single_company(matches)
            else ResolutionStatus.AMBIGUOUS
        )

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
        value = re.sub(r"[^a-z0-9]+", " ", value)
        return " ".join(value.split())