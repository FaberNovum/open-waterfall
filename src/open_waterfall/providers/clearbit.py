from __future__ import annotations

import base64
from typing import Optional

from open_waterfall.core.models.company import Company, CompanyEnrichmentResult, FundingInfo, HiringSignals
from open_waterfall.core.models.contact import Contact, ContactEnrichmentResult
from open_waterfall.core.providers.base import BaseEnricher


class ClearbitEnricher(BaseEnricher):
    name = "clearbit"
    base_url = "https://company.clearbit.com/v2"
    person_url = "https://person.clearbit.com/v2"

    def _get_headers(self) -> dict[str, str]:
        auth_string = base64.b64encode(f"{self.api_key}:".encode()).decode()
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Basic {auth_string}",
        }

    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        try:
            response = self.client.get(f"{self.base_url}/companies/find", params={"domain": domain})
            response.raise_for_status()
            data = response.json()
            if not data:
                return CompanyEnrichmentResult(success=False, source=self.name, error="No company data found")
            company = self._create_company_from_response(data)
            fields_enriched = [
                field_name
                for field_name in Company.model_fields
                if getattr(company, field_name) is not None
                and field_name not in ("domain", "enrichment_sources", "enriched_at")
            ]
            return CompanyEnrichmentResult(
                success=True,
                company=company,
                source=self.name,
                fields_enriched=fields_enriched,
                raw_response=data,
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
            email_patterns = [
                f"{first_name.lower()}.{last_name.lower()}@{domain}",
                f"{first_name.lower()[0]}{last_name.lower()}@{domain}",
                f"{first_name.lower()}@{domain}",
                f"{first_name.lower()}{last_name.lower()}@{domain}",
            ]
            for email in email_patterns:
                try:
                    response = self.client.get(f"{self.person_url}/people/find", params={"email": email})
                    if response.status_code != 200:
                        continue
                    data = response.json()
                    if not data:
                        continue
                    contact = self._create_contact_from_response(data)
                    contact.email = email
                    contact.company_domain = domain
                    contact.company_name = company_name
                    fields_enriched = [
                        field_name
                        for field_name in Contact.model_fields
                        if getattr(contact, field_name) is not None
                        and field_name not in (
                            "company_domain",
                            "company_name",
                            "enrichment_sources",
                            "enriched_at",
                            "icp_score",
                            "intent_score",
                            "total_score",
                            "segment",
                            "email_verification_status",
                            "external_ids",
                        )
                    ]
                    return ContactEnrichmentResult(
                        success=True,
                        contact=contact,
                        source=self.name,
                        fields_enriched=fields_enriched,
                        raw_response=data,
                    )
                except Exception:
                    continue
            return ContactEnrichmentResult(
                success=False,
                source=self.name,
                error="No contact found with common email patterns",
            )
        except Exception as exc:
            return ContactEnrichmentResult(success=False, source=self.name, error=str(exc))

    def _create_company_from_response(self, data: dict) -> Company:
        metrics = data.get("metrics", {})
        geo = data.get("geo", {})
        funding_info = FundingInfo(total_raised=metrics.get("raised")) if metrics.get("raised") else None
        hiring_info = HiringSignals(growth_rate=metrics.get("employeesGrowth")) if metrics.get("employees") else None
        linkedin_handle = data.get("linkedin", {}).get("handle")
        twitter_handle = data.get("twitter", {}).get("handle")
        facebook_handle = data.get("facebook", {}).get("handle")
        crunchbase_handle = data.get("crunchbase", {}).get("handle")
        return Company(
            domain=data.get("domain", ""),
            name=data.get("name"),
            industry=data.get("category", {}).get("industry"),
            sub_industry=data.get("category", {}).get("subIndustry"),
            employee_count=metrics.get("employees"),
            employee_range=metrics.get("employeesRange"),
            revenue=metrics.get("estimatedAnnualRevenue"),
            founded_year=data.get("foundedYear"),
            headquarters_city=geo.get("city"),
            headquarters_state=geo.get("stateCode"),
            headquarters_country=geo.get("country"),
            address=geo.get("streetAddress"),
            tech_stack=data.get("tech", []),
            linkedin_url=f"https://linkedin.com/company/{linkedin_handle}" if linkedin_handle else None,
            twitter_url=f"https://twitter.com/{twitter_handle}" if twitter_handle else None,
            facebook_url=f"https://facebook.com/{facebook_handle}" if facebook_handle else None,
            crunchbase_url=f"https://crunchbase.com/organization/{crunchbase_handle}" if crunchbase_handle else None,
            funding=funding_info,
            hiring=hiring_info,
            description=data.get("description"),
            is_b2b=data.get("type") == "B2B",
        )

    def _create_contact_from_response(self, data: dict) -> Contact:
        name = data.get("name", {})
        employment = data.get("employment", {})
        geo = data.get("geo", {})
        linkedin_handle = data.get("linkedin", {}).get("handle")
        twitter_handle = data.get("twitter", {}).get("handle")
        return Contact(
            first_name=name.get("givenName"),
            last_name=name.get("familyName"),
            full_name=name.get("fullName"),
            title=employment.get("title"),
            seniority=employment.get("seniority"),
            linkedin_url=f"https://linkedin.com/in/{linkedin_handle}" if linkedin_handle else None,
            twitter_url=f"https://twitter.com/{twitter_handle}" if twitter_handle else None,
            city=geo.get("city"),
            state=geo.get("stateCode"),
            country=geo.get("country"),
        )
