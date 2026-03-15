from __future__ import annotations

from typing import Optional

from open_waterfall.core.models.company import Company, CompanyEnrichmentResult
from open_waterfall.core.models.contact import Contact, ContactEnrichmentResult
from open_waterfall.core.providers.base import BaseEnricher


class ProspeoEnricher(BaseEnricher):
    name = "prospeo"
    base_url = "https://api.prospeo.io"

    def _get_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-KEY": self.api_key,
        }

    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        try:
            response = self._make_request("POST", "/domain-search", json_data={"domain": domain})
            if response.get("error"):
                return CompanyEnrichmentResult(
                    success=False,
                    source=self.name,
                    error=response.get("message", "Unknown error"),
                )
            company = Company(domain=domain, name=response.get("company_name"))
            fields_enriched = ["name"] if company.name else []
            return CompanyEnrichmentResult(
                success=bool(company.name),
                company=company if company.name else None,
                source=self.name,
                fields_enriched=fields_enriched,
                raw_response=response,
            )
        except Exception as exc:
            return CompanyEnrichmentResult(success=False, source=self.name, error=str(exc))

    def enrich_contact(
        self,
        first_name: str,
        last_name: str,
        domain: str,
        company_name: Optional[str] = None,
    ) -> ContactEnrichmentResult:
        try:
            response = self._make_request(
                "POST",
                "/email-finder",
                json_data={"first_name": first_name, "last_name": last_name, "company": domain},
            )
            if response.get("error"):
                return ContactEnrichmentResult(
                    success=False,
                    source=self.name,
                    error=response.get("message", "No email found"),
                )
            email = response.get("email")
            if not email:
                return ContactEnrichmentResult(success=False, source=self.name, error="No email found")
            contact = Contact(
                first_name=first_name,
                last_name=last_name,
                full_name=f"{first_name} {last_name}",
                email=email,
                company_domain=domain,
                company_name=company_name or response.get("company_name"),
            )
            fields_enriched = ["email"]
            if response.get("phone"):
                contact.phone = response.get("phone")
                fields_enriched.append("phone")
            if response.get("linkedin_url"):
                contact.linkedin_url = response.get("linkedin_url")
                fields_enriched.append("linkedin_url")
            return ContactEnrichmentResult(
                success=True,
                contact=contact,
                source=self.name,
                fields_enriched=fields_enriched,
                raw_response=response,
            )
        except Exception as exc:
            return ContactEnrichmentResult(success=False, source=self.name, error=str(exc))

    def find_by_linkedin(self, linkedin_url: str) -> ContactEnrichmentResult:
        try:
            response = self._make_request("POST", "/linkedin-email-finder", json_data={"url": linkedin_url})
            if response.get("error"):
                return ContactEnrichmentResult(
                    success=False,
                    source=self.name,
                    error=response.get("message", "No data found"),
                )
            contact = Contact(
                first_name=response.get("first_name"),
                last_name=response.get("last_name"),
                full_name=response.get("full_name"),
                email=response.get("email"),
                phone=response.get("phone"),
                linkedin_url=linkedin_url,
                title=response.get("title"),
                company_name=response.get("company"),
            )
            fields_enriched = [
                field_name
                for field_name in ["email", "phone", "title", "first_name", "last_name"]
                if getattr(contact, field_name)
            ]
            return ContactEnrichmentResult(
                success=bool(contact.email),
                contact=contact if contact.email else None,
                source=self.name,
                fields_enriched=fields_enriched,
                raw_response=response,
            )
        except Exception as exc:
            return ContactEnrichmentResult(success=False, source=self.name, error=str(exc))
