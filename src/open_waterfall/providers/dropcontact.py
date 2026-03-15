from __future__ import annotations

from typing import Optional

from open_waterfall.core.models.company import Company, CompanyEnrichmentResult
from open_waterfall.core.models.contact import Contact, ContactEnrichmentResult
from open_waterfall.core.providers.base import BaseEnricher


class DropcontactEnricher(BaseEnricher):
    name = "dropcontact"
    base_url = "https://api.dropcontact.io"

    def _get_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Access-Token": self.api_key,
        }

    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        try:
            response = self._make_request(
                "POST",
                "/batch",
                json_data={"data": [{"website": domain}], "enrich": True},
            )
            if response.get("error"):
                return CompanyEnrichmentResult(
                    success=False,
                    source=self.name,
                    error=response.get("reason", "Unknown error"),
                )
            data = response.get("data", [{}])[0] if response.get("data") else {}
            company = Company(domain=domain, name=data.get("company"))
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
            payload = {
                "data": [{"first_name": first_name, "last_name": last_name, "website": domain}],
                "enrich": True,
                "siren": True,
            }
            if company_name:
                payload["data"][0]["company"] = company_name
            response = self._make_request("POST", "/batch", json_data=payload)
            if response.get("error"):
                return ContactEnrichmentResult(
                    success=False,
                    source=self.name,
                    error=response.get("reason", "No contact found"),
                )
            data = response.get("data", [{}])[0] if response.get("data") else {}
            if not data.get("email"):
                return ContactEnrichmentResult(success=False, source=self.name, error="No email found")
            contact = self._create_contact_from_response(data)
            contact.first_name = data.get("first_name", first_name)
            contact.last_name = data.get("last_name", last_name)
            contact.company_domain = domain
            contact.company_name = company_name or data.get("company")
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
                raw_response=response,
            )
        except Exception as exc:
            return ContactEnrichmentResult(success=False, source=self.name, error=str(exc))

    def _create_contact_from_response(self, data: dict) -> Contact:
        email = data["email"][0] if isinstance(data.get("email"), list) and data.get("email") else data.get("email")
        phone = None
        mobile = None
        if data.get("phone"):
            phones = data["phone"] if isinstance(data["phone"], list) else [data["phone"]]
            for entry in phones:
                if isinstance(entry, dict):
                    if entry.get("type") == "mobile":
                        mobile = entry.get("number")
                    else:
                        phone = phone or entry.get("number")
                else:
                    phone = phone or entry
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        return Contact(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name if full_name else None,
            email=email,
            phone=phone,
            mobile=mobile,
            title=data.get("job_title"),
            linkedin_url=data.get("linkedin"),
            city=data.get("city"),
            country=data.get("country"),
        )
