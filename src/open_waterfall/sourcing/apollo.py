from __future__ import annotations

import math
from typing import Optional

from open_waterfall.core.config.schema import SourceConfig
from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact
from open_waterfall.providers.apollo import ApolloEnricher
from open_waterfall.sourcing.base import BaseLeadSource


class ApolloLeadSource(BaseLeadSource):
    name = "apollo"

    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        self.enricher = ApolloEnricher(api_key=api_key, timeout=timeout)

    def search(self, config: SourceConfig) -> list[tuple[Contact, Optional[Company]]]:
        page_size = max(1, min(config.page_size, 100))
        max_results = max(1, config.max_results)
        max_pages = max(1, math.ceil(max_results / page_size))
        lead_pairs: list[tuple[Contact, Optional[Company]]] = []
        seen_keys: set[tuple[str, str, str]] = set()

        for page in range(1, max_pages + 1):
            search_result = self.enricher.search_people(
                person_titles=config.filters.titles or None,
                person_seniorities=config.filters.seniorities or None,
                organization_locations=config.filters.locations or None,
                organization_num_employees_ranges=config.filters.employee_ranges or None,
                contact_email_status=config.filters.email_status or None,
                page=page,
                per_page=page_size,
            )

            for person in search_result.people:
                contact, company = self._lead_pair_from_person(person)
                dedupe_key = self._dedupe_key(contact)
                if dedupe_key in seen_keys:
                    continue
                seen_keys.add(dedupe_key)
                lead_pairs.append((contact, company))
                if len(lead_pairs) >= max_results:
                    return lead_pairs

            if len(search_result.people) < page_size:
                break

        return lead_pairs

    def _lead_pair_from_person(self, person: dict) -> tuple[Contact, Optional[Company]]:
        organization = person.get("organization", {}) or {}
        domain = organization.get("primary_domain") or organization.get("domain")

        contact = Contact(
            first_name=person.get("first_name"),
            last_name=person.get("last_name"),
            full_name=person.get("name"),
            company_domain=domain,
            company_name=organization.get("name"),
            email=person.get("email"),
            title=person.get("title"),
            seniority=person.get("seniority"),
            department=person.get("department"),
            linkedin_url=person.get("linkedin_url"),
            city=person.get("city"),
            state=person.get("state"),
            country=person.get("country"),
            enrichment_sources=[self.name],
            external_ids={"apollo_person_id": str(person["id"])} if person.get("id") else {},
        )

        company = None
        if domain or organization.get("name"):
            company = Company(
                domain=domain or "",
                name=organization.get("name"),
                industry=organization.get("industry"),
                employee_count=organization.get("estimated_num_employees"),
                revenue=organization.get("annual_revenue"),
                linkedin_url=organization.get("linkedin_url"),
                description=organization.get("short_description"),
                website_context=organization.get("organization_headline"),
                tech_stack=organization.get("technologies", []) or [],
                enrichment_sources=[self.name],
            )

        return contact, company

    def _dedupe_key(self, contact: Contact) -> tuple[str, str, str]:
        email = (contact.email or "").strip().lower()
        linkedin_url = (contact.linkedin_url or "").strip().lower()
        name_domain = (
            (contact.full_name or f"{contact.first_name or ''} {contact.last_name or ''}").strip().lower(),
            (contact.company_domain or "").strip().lower(),
        )
        return (email, linkedin_url, "::".join(name_domain))
