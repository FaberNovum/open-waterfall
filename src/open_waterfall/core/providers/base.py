from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from open_waterfall.core.models.company import Company, CompanyEnrichmentResult
from open_waterfall.core.models.contact import Contact, ContactEnrichmentResult


class BaseEnricher(ABC):
    """Abstract enrichment provider interface."""

    name: str = "base"
    base_url: str = ""

    def __init__(self, api_key: str = "", timeout: float = 30.0):
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout, headers=self._get_headers())
        return self._client

    def _get_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        response = self.client.request(method, f"{self.base_url}{endpoint}", params=params, json=json_data)
        response.raise_for_status()
        return response.json()

    @abstractmethod
    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        """Return company enrichment result."""

    @abstractmethod
    def enrich_contact(
        self,
        first_name: str,
        last_name: str,
        domain: str,
        company_name: Optional[str] = None,
    ) -> ContactEnrichmentResult:
        """Return contact enrichment result."""

    def _create_company_from_response(self, data: dict) -> Company:
        return Company(domain=data.get("domain", ""))

    def _create_contact_from_response(self, data: dict) -> Contact:
        return Contact()

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "BaseEnricher":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

