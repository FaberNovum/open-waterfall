from __future__ import annotations

from typing import Optional

from open_waterfall.core.models.company import Company, CompanyEnrichmentResult
from open_waterfall.core.models.contact import Contact, ContactEnrichmentResult, EmailVerificationStatus
from open_waterfall.core.providers.base import BaseEnricher


class DemoEnricher(BaseEnricher):
    """Deterministic no-credentials provider used for local demos and tests."""

    name = "demo"

    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        normalized_domain = domain.strip().lower() or "example.com"
        company = Company(
            domain=normalized_domain,
            name="Example",
            industry="SaaS",
            employee_count=200,
            revenue=5000000,
            tech_stack=["Salesforce", "HubSpot", "Marketo"],
            website_context="Example helps operations teams automate handoffs and qualification.",
            description="Workflow automation for operations-heavy revenue teams.",
            enrichment_sources=[self.name],
        )
        return CompanyEnrichmentResult(
            success=True,
            company=company,
            source=self.name,
            fields_enriched=["name", "industry", "employee_count", "revenue", "tech_stack", "website_context"],
            raw_response={"domain": normalized_domain, "demo": True},
        )

    def enrich_contact(
        self,
        first_name: str,
        last_name: str,
        domain: str,
        company_name: Optional[str] = None,
    ) -> ContactEnrichmentResult:
        normalized_domain = domain.strip().lower() or "example.com"
        normalized_first = (first_name or "Jane").strip() or "Jane"
        normalized_last = (last_name or "Doe").strip() or "Doe"
        contact = Contact(
            first_name=normalized_first,
            last_name=normalized_last,
            full_name=f"{normalized_first} {normalized_last}".strip(),
            company_domain=normalized_domain,
            company_name=company_name or "Example",
            email=f"{normalized_first.lower()}.{normalized_last.lower()}@{normalized_domain}",
            phone="312-555-0100",
            mobile="312-555-0101",
            title="VP Operations",
            seniority="vp",
            department="operations",
            linkedin_url="https://linkedin.com/in/example-jane-doe",
            twitter_url="https://twitter.com/example_jane",
            city="Chicago",
            state="IL",
            country="United States",
            email_verification_status=EmailVerificationStatus.VALID,
            enrichment_sources=[self.name],
        )
        return ContactEnrichmentResult(
            success=True,
            contact=contact,
            source=self.name,
            fields_enriched=[
                "email",
                "phone",
                "mobile",
                "title",
                "seniority",
                "department",
                "linkedin_url",
                "twitter_url",
                "city",
                "state",
                "country",
            ],
            raw_response={"domain": normalized_domain, "demo": True},
        )
