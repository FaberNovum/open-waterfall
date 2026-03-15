from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from open_waterfall.core.models.company import Company, CompanyEnrichmentResult, FundingInfo, HiringSignals
from open_waterfall.core.models.contact import Contact, ContactEnrichmentResult
from open_waterfall.core.providers.base import BaseEnricher


@dataclass
class ApolloSearchResult:
    people: List[dict] = field(default_factory=list)
    total_entries: int = 0
    page: int = 1
    per_page: int = 100


class ApolloEnricher(BaseEnricher):
    name = "apollo"
    base_url = "https://api.apollo.io/v1"

    def _get_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Api-Key": self.api_key,
        }

    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        try:
            response = self._make_request("POST", "/organizations/enrich", json_data={"domain": domain})
            org = response.get("organization", {})
            if not org:
                return CompanyEnrichmentResult(success=False, source=self.name, error="No organization data found")
            company = self._create_company_from_response(org)
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
                "first_name": first_name,
                "last_name": last_name,
                "organization_domains": [domain],
            }
            if company_name:
                payload["organization_name"] = company_name
            response = self._make_request("POST", "/people/match", json_data=payload)
            person = response.get("person", {})
            if not person:
                return ContactEnrichmentResult(success=False, source=self.name, error="No contact found")
            contact = self._create_contact_from_response(person)
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
                raw_response=response,
            )
        except Exception as exc:
            return ContactEnrichmentResult(success=False, source=self.name, error=str(exc))

    def _create_company_from_response(self, data: dict) -> Company:
        funding_info = None
        if data.get("total_funding") or data.get("latest_funding_round_date"):
            funding_info = FundingInfo(
                total_raised=data.get("total_funding"),
                last_round_type=data.get("latest_funding_stage"),
                last_round_amount=data.get("latest_funding_round_amount"),
            )

        hiring_info = None
        if data.get("estimated_num_employees"):
            hiring_info = HiringSignals(
                open_positions=data.get("num_open_jobs", 0),
                departments_hiring=data.get("departments_hiring", []),
            )

        return Company(
            domain=data.get("primary_domain", data.get("domain", "")),
            name=data.get("name"),
            industry=data.get("industry"),
            sub_industry=data.get("sub_industry"),
            employee_count=data.get("estimated_num_employees"),
            employee_range=data.get("employee_range"),
            revenue=data.get("annual_revenue"),
            revenue_range=data.get("annual_revenue_printed"),
            founded_year=data.get("founded_year"),
            headquarters_city=data.get("city"),
            headquarters_state=data.get("state"),
            headquarters_country=data.get("country"),
            address=data.get("raw_address"),
            tech_stack=data.get("technologies", []),
            linkedin_url=data.get("linkedin_url"),
            twitter_url=data.get("twitter_url"),
            facebook_url=data.get("facebook_url"),
            crunchbase_url=data.get("crunchbase_url"),
            funding=funding_info,
            hiring=hiring_info,
            description=data.get("long_description"),
            short_description=data.get("short_description"),
            is_public=data.get("publicly_traded_exchange") is not None,
            stock_symbol=data.get("publicly_traded_symbol"),
        )

    def _create_contact_from_response(self, data: dict) -> Contact:
        return Contact(
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            full_name=data.get("name"),
            email=data.get("email"),
            phone=data.get("phone_numbers", [{}])[0].get("sanitized_number") if data.get("phone_numbers") else None,
            mobile=next(
                (
                    phone.get("sanitized_number")
                    for phone in data.get("phone_numbers", [])
                    if phone.get("type") == "mobile"
                ),
                None,
            ),
            title=data.get("title"),
            seniority=data.get("seniority"),
            department=data.get("department"),
            linkedin_url=data.get("linkedin_url"),
            twitter_url=data.get("twitter_url"),
            city=data.get("city"),
            state=data.get("state"),
            country=data.get("country"),
        )

    def search_people(
        self,
        person_titles: Optional[List[str]] = None,
        person_seniorities: Optional[List[str]] = None,
        organization_locations: Optional[List[str]] = None,
        organization_num_employees_ranges: Optional[List[str]] = None,
        contact_email_status: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 100,
    ) -> ApolloSearchResult:
        payload = {"per_page": min(per_page, 100), "page": min(page, 500)}
        if person_titles:
            payload["person_titles"] = person_titles
        if person_seniorities:
            payload["person_seniorities"] = person_seniorities
        if organization_locations:
            payload["organization_locations"] = organization_locations
        if organization_num_employees_ranges:
            payload["organization_num_employees_ranges"] = organization_num_employees_ranges
        if contact_email_status:
            payload["contact_email_status"] = contact_email_status
        response = self._make_request("POST", "/mixed_people/api_search", json_data=payload)
        return ApolloSearchResult(
            people=response.get("people", []),
            total_entries=response.get("total_entries", 0),
            page=page,
            per_page=per_page,
        )

    def enrich_person_by_id(self, person_id: str) -> ContactEnrichmentResult:
        try:
            response = self._make_request("POST", "/people/enrich", json_data={"id": person_id})
            person = response.get("person", {})
            if not person:
                return ContactEnrichmentResult(success=False, source=self.name, error="No contact found")
            contact = self._create_contact_from_response(person)
            return ContactEnrichmentResult(
                success=True,
                contact=contact,
                source=self.name,
                fields_enriched=["email", "phone", "linkedin_url"],
                raw_response=response,
            )
        except Exception as exc:
            return ContactEnrichmentResult(success=False, source=self.name, error=str(exc))

    def search_and_enrich_people(
        self,
        person_titles: Optional[List[str]] = None,
        person_seniorities: Optional[List[str]] = None,
        organization_locations: Optional[List[str]] = None,
        organization_num_employees_ranges: Optional[List[str]] = None,
        contact_email_status: Optional[List[str]] = None,
        max_pages: int = 1,
        delay: float = 1.0,
    ) -> list[Contact]:
        contacts: list[Contact] = []
        for page in range(1, max_pages + 1):
            search_result = self.search_people(
                person_titles=person_titles,
                person_seniorities=person_seniorities,
                organization_locations=organization_locations,
                organization_num_employees_ranges=organization_num_employees_ranges,
                contact_email_status=contact_email_status,
                page=page,
            )
            for person in search_result.people:
                contact = Contact(
                    first_name=person.get("first_name"),
                    last_name=person.get("last_name"),
                    company_name=person.get("organization", {}).get("name"),
                    company_domain=person.get("organization", {}).get("primary_domain"),
                    title=person.get("title"),
                    seniority=person.get("seniority"),
                    department=person.get("department"),
                    linkedin_url=person.get("linkedin_url"),
                    city=person.get("city"),
                    state=person.get("state"),
                    country=person.get("country"),
                )
                contacts.append(contact)
            if page < max_pages:
                time.sleep(delay)
        return contacts
