from __future__ import annotations

from typing import Optional

from open_waterfall.core.models.company import Company, CompanyEnrichmentResult, FundingInfo, HiringSignals
from open_waterfall.core.models.contact import Contact, ContactEnrichmentResult
from open_waterfall.core.providers.base import BaseEnricher


class ZoomInfoEnricher(BaseEnricher):
    name = "zoominfo"
    base_url = "https://api.zoominfo.com"

    def __init__(self, api_key: str, client_id: str = "", timeout: float = 30.0):
        super().__init__(api_key, timeout)
        self.client_id = client_id
        self._access_token: Optional[str] = None

    def _get_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        try:
            response = self._make_request(
                "POST",
                "/enrich/company",
                json_data={
                    "matchCompanyInput": [{"companyWebsite": domain}],
                    "outputFields": [
                        "id",
                        "name",
                        "website",
                        "revenue",
                        "employeeCount",
                        "industry",
                        "subIndustry",
                        "city",
                        "state",
                        "country",
                        "yearFounded",
                        "linkedInUrl",
                        "twitterUrl",
                        "technologies",
                        "fundingInfo",
                        "jobPostings",
                        "description",
                    ],
                },
            )
            data = response.get("data", {}).get("result", [])
            if not data or not data[0].get("data"):
                return CompanyEnrichmentResult(success=False, source=self.name, error="No company data found")
            company_data = data[0]["data"][0]
            company = self._create_company_from_response(company_data)
            company.domain = domain
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
            match_input = {"firstName": first_name, "lastName": last_name, "companyWebsite": domain}
            if company_name:
                match_input["companyName"] = company_name
            response = self._make_request(
                "POST",
                "/enrich/contact",
                json_data={
                    "matchPersonInput": [match_input],
                    "outputFields": [
                        "id",
                        "firstName",
                        "lastName",
                        "email",
                        "phone",
                        "mobilePhone",
                        "jobTitle",
                        "department",
                        "managementLevel",
                        "linkedInUrl",
                        "city",
                        "state",
                        "country",
                    ],
                },
            )
            data = response.get("data", {}).get("result", [])
            if not data or not data[0].get("data"):
                return ContactEnrichmentResult(success=False, source=self.name, error="No contact found")
            contact_data = data[0]["data"][0]
            contact = self._create_contact_from_response(contact_data)
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
        if data.get("fundingInfo"):
            funding_info = FundingInfo(
                total_raised=data["fundingInfo"].get("totalFundingAmount"),
                last_round_type=data["fundingInfo"].get("lastFundingRoundType"),
                last_round_amount=data["fundingInfo"].get("lastFundingAmount"),
            )
        hiring_info = HiringSignals(open_positions=len(data.get("jobPostings", []))) if data.get("jobPostings") else None
        return Company(
            domain=data.get("website", ""),
            name=data.get("name"),
            industry=data.get("industry"),
            sub_industry=data.get("subIndustry"),
            employee_count=data.get("employeeCount"),
            revenue=data.get("revenue"),
            founded_year=data.get("yearFounded"),
            headquarters_city=data.get("city"),
            headquarters_state=data.get("state"),
            headquarters_country=data.get("country"),
            tech_stack=data.get("technologies", []),
            linkedin_url=data.get("linkedInUrl"),
            twitter_url=data.get("twitterUrl"),
            funding=funding_info,
            hiring=hiring_info,
            description=data.get("description"),
        )

    def _create_contact_from_response(self, data: dict) -> Contact:
        return Contact(
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            full_name=f"{data.get('firstName', '')} {data.get('lastName', '')}".strip(),
            email=data.get("email"),
            phone=data.get("phone"),
            mobile=data.get("mobilePhone"),
            title=data.get("jobTitle"),
            seniority=data.get("managementLevel"),
            department=data.get("department"),
            linkedin_url=data.get("linkedInUrl"),
            city=data.get("city"),
            state=data.get("state"),
            country=data.get("country"),
        )
