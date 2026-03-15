from __future__ import annotations

from datetime import datetime
from typing import Optional

from open_waterfall.core.models.company import Company, CompanyEnrichmentResult
from open_waterfall.core.models.contact import Contact, ContactEnrichmentResult
from open_waterfall.core.providers.base import BaseEnricher


class WaterfallProcessor:
    """Cascade enrichment through ordered providers."""

    def __init__(
        self,
        company_enrichers: list[BaseEnricher],
        contact_enrichers: list[BaseEnricher],
        merge_results: bool = True,
    ):
        self.company_enrichers = company_enrichers
        self.contact_enrichers = contact_enrichers
        self.merge_results = merge_results

    def enrich_company(
        self,
        domain: str,
        required_fields: Optional[list[str]] = None,
    ) -> tuple[Optional[Company], list[CompanyEnrichmentResult]]:
        results: list[CompanyEnrichmentResult] = []
        merged_company: Optional[Company] = None
        sources: list[str] = []

        for enricher in self.company_enrichers:
            result = enricher.enrich_company(domain)
            results.append(result)

            if result.success and result.company:
                sources.append(result.source)
                if merged_company is None:
                    merged_company = result.company.model_copy(deep=True)
                elif self.merge_results:
                    merged_company = self._merge_companies(merged_company, result.company)

                if required_fields and merged_company:
                    missing = self._get_missing_fields(merged_company, required_fields)
                    if not missing:
                        break

                if not self.merge_results:
                    break

        if merged_company:
            merged_company.enrichment_sources = sources
            merged_company.enriched_at = datetime.utcnow()

        return merged_company, results

    def enrich_contact(
        self,
        first_name: str,
        last_name: str,
        domain: str,
        company_name: Optional[str] = None,
        required_fields: Optional[list[str]] = None,
    ) -> tuple[Optional[Contact], list[ContactEnrichmentResult]]:
        results: list[ContactEnrichmentResult] = []
        merged_contact: Optional[Contact] = None
        sources: list[str] = []

        for enricher in self.contact_enrichers:
            result = enricher.enrich_contact(
                first_name=first_name,
                last_name=last_name,
                domain=domain,
                company_name=company_name,
            )
            results.append(result)

            if result.success and result.contact:
                sources.append(result.source)
                if merged_contact is None:
                    merged_contact = result.contact.model_copy(deep=True)
                elif self.merge_results:
                    merged_contact = self._merge_contacts(merged_contact, result.contact)

                if required_fields and merged_contact:
                    missing = self._get_missing_fields(merged_contact, required_fields)
                    if not missing:
                        break

                if not self.merge_results:
                    break

        if merged_contact:
            merged_contact.enrichment_sources = sources
            merged_contact.enriched_at = datetime.utcnow()
            merged_contact.first_name = merged_contact.first_name or first_name
            merged_contact.last_name = merged_contact.last_name or last_name
            merged_contact.company_domain = domain
            merged_contact.company_name = merged_contact.company_name or company_name

        return merged_contact, results

    def _merge_companies(self, base: Company, new: Company) -> Company:
        merged_data = base.model_dump()
        for field, value in new.model_dump().items():
            if field in ("enrichment_sources", "enriched_at"):
                continue
            if merged_data.get(field) is None and value is not None:
                merged_data[field] = value
            elif isinstance(merged_data.get(field), list) and isinstance(value, list):
                merged_data[field] = list(set(merged_data[field]).union(set(value)))
        return Company(**merged_data)

    def _merge_contacts(self, base: Contact, new: Contact) -> Contact:
        merged_data = base.model_dump()
        for field, value in new.model_dump().items():
            if field in (
                "enrichment_sources",
                "enriched_at",
                "icp_score",
                "intent_score",
                "total_score",
                "segment",
                "email_verification_status",
            ):
                continue
            if merged_data.get(field) is None and value is not None:
                merged_data[field] = value
            elif isinstance(merged_data.get(field), list) and isinstance(value, list):
                merged_data[field] = list(set(merged_data[field]).union(set(value)))
        return Contact(**merged_data)

    def _get_missing_fields(self, model: object, required_fields: list[str]) -> list[str]:
        missing = []
        for field in required_fields:
            value = getattr(model, field, None)
            if value is None or (isinstance(value, list) and not value):
                missing.append(field)
        return missing
