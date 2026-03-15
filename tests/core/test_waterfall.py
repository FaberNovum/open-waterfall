from typing import Optional

from open_waterfall.core.models.company import Company, CompanyEnrichmentResult
from open_waterfall.core.models.contact import Contact, ContactEnrichmentResult
from open_waterfall.core.pipeline.waterfall import WaterfallProcessor


class MockEnricher:
    def __init__(self, name: str, company_data: Optional[dict] = None, contact_data: Optional[dict] = None):
        self.name = name
        self._company_data = company_data
        self._contact_data = contact_data

    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        if self._company_data:
            return CompanyEnrichmentResult(
                success=True,
                company=Company(domain=domain, **self._company_data),
                source=self.name,
                fields_enriched=list(self._company_data.keys()),
            )
        return CompanyEnrichmentResult(success=False, source=self.name, error="No data found")

    def enrich_contact(self, first_name: str, last_name: str, domain: str, company_name: Optional[str] = None):
        if self._contact_data:
            return ContactEnrichmentResult(
                success=True,
                contact=Contact(first_name=first_name, last_name=last_name, company_domain=domain, **self._contact_data),
                source=self.name,
                fields_enriched=list(self._contact_data.keys()),
            )
        return ContactEnrichmentResult(success=False, source=self.name, error="No data found")


def test_company_enrichment_merge() -> None:
    enrichers = [
        MockEnricher("apollo", company_data={"name": "Acme", "industry": "Tech"}),
        MockEnricher("clearbit", company_data={"employee_count": 100}),
    ]
    processor = WaterfallProcessor(company_enrichers=enrichers, contact_enrichers=[], merge_results=True)
    company, results = processor.enrich_company("acme.com")

    assert company is not None
    assert company.name == "Acme"
    assert company.employee_count == 100
    assert len(results) == 2


def test_contact_enrichment_first_provider_only() -> None:
    enrichers = [
        MockEnricher("apollo", contact_data={"email": "john@acme.com"}),
        MockEnricher("hunter", contact_data={"phone": "555-1234"}),
    ]
    processor = WaterfallProcessor(company_enrichers=[], contact_enrichers=enrichers, merge_results=False)
    contact, results = processor.enrich_contact("John", "Doe", "acme.com")

    assert contact is not None
    assert contact.email == "john@acme.com"
    assert len(results) == 1
