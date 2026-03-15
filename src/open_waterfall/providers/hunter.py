from __future__ import annotations

from typing import Optional

from open_waterfall.core.models.company import Company, CompanyEnrichmentResult
from open_waterfall.core.models.contact import Contact, ContactEnrichmentResult
from open_waterfall.core.providers.base import BaseEnricher


class HunterEnricher(BaseEnricher):
    name = "hunter"
    base_url = "https://api.hunter.io/v2"

    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        try:
            response = self._make_request("GET", "/domain-search", params={"domain": domain, "api_key": self.api_key})
            data = response.get("data", {})
            if not data:
                return CompanyEnrichmentResult(success=False, source=self.name, error="No company data found")
            company = Company(domain=domain, name=data.get("organization"), industry=data.get("industry"))
            fields_enriched = ["name"] if company.name else []
            if company.industry:
                fields_enriched.append("industry")
            return CompanyEnrichmentResult(
                success=True,
                company=company,
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
                "GET",
                "/email-finder",
                params={
                    "domain": domain,
                    "first_name": first_name,
                    "last_name": last_name,
                    "api_key": self.api_key,
                },
            )
            data = response.get("data", {})
            if not data or not data.get("email"):
                return ContactEnrichmentResult(success=False, source=self.name, error="No email found")
            contact = self._create_contact_from_response(data)
            contact.first_name = first_name
            contact.last_name = last_name
            contact.full_name = f"{first_name} {last_name}"
            contact.company_domain = domain
            contact.company_name = company_name
            fields_enriched = ["email"]
            if contact.linkedin_url:
                fields_enriched.append("linkedin_url")
            if contact.twitter_url:
                fields_enriched.append("twitter_url")
            if contact.phone:
                fields_enriched.append("phone")
            if contact.title:
                fields_enriched.append("title")
            return ContactEnrichmentResult(
                success=True,
                contact=contact,
                source=self.name,
                fields_enriched=fields_enriched,
                raw_response=response,
            )
        except Exception as exc:
            return ContactEnrichmentResult(success=False, source=self.name, error=str(exc))

    def _create_contact_from_response(self, data: dict) -> Contact:
        linkedin_url = None
        twitter_url = None
        for source in data.get("sources", []):
            if "linkedin.com" in source.get("uri", ""):
                linkedin_url = source.get("uri")
            elif "twitter.com" in source.get("uri", ""):
                twitter_url = source.get("uri")
        return Contact(
            email=data.get("email"),
            title=data.get("position"),
            linkedin_url=linkedin_url,
            twitter_url=twitter_url,
            phone=data.get("phone_number"),
        )

    def verify_email(self, email: str) -> dict:
        try:
            response = self._make_request(
                "GET",
                "/email-verifier",
                params={"email": email, "api_key": self.api_key},
            )
            data = response.get("data", {})
            return {
                "email": email,
                "status": data.get("status"),
                "score": data.get("score"),
                "regexp": data.get("regexp"),
                "gibberish": data.get("gibberish"),
                "disposable": data.get("disposable"),
                "webmail": data.get("webmail"),
                "mx_records": data.get("mx_records"),
                "smtp_server": data.get("smtp_server"),
                "smtp_check": data.get("smtp_check"),
                "accept_all": data.get("accept_all"),
            }
        except Exception as exc:
            return {"email": email, "status": "error", "error": str(exc)}
