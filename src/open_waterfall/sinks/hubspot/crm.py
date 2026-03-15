from __future__ import annotations

from typing import Any, Optional

from open_waterfall.core.config.schema import HubSpotSinkConfig
from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact
from open_waterfall.messaging.parser import parse_email_steps
from open_waterfall.sinks.base import LeadSink
from open_waterfall.sinks.hubspot.workflow import HubSpotWorkflowClient


HUBSPOT_INDUSTRIES = {
    "ACCOUNTING",
    "AIRLINES_AVIATION",
    "ALTERNATIVE_DISPUTE_RESOLUTION",
    "ALTERNATIVE_MEDICINE",
    "ANIMATION",
    "APPAREL_FASHION",
    "ARCHITECTURE_PLANNING",
    "ARTS_AND_CRAFTS",
    "AUTOMOTIVE",
    "AVIATION_AEROSPACE",
    "BANKING",
    "BIOTECHNOLOGY",
    "BROADCAST_MEDIA",
    "BUILDING_MATERIALS",
    "BUSINESS_SUPPLIES_AND_EQUIPMENT",
    "CAPITAL_MARKETS",
    "CHEMICALS",
    "CIVIC_SOCIAL_ORGANIZATION",
    "CIVIL_ENGINEERING",
    "COMMERCIAL_REAL_ESTATE",
    "COMPUTER_NETWORK_SECURITY",
    "COMPUTER_GAMES",
    "COMPUTER_HARDWARE",
    "COMPUTER_NETWORKING",
    "COMPUTER_SOFTWARE",
    "INTERNET",
    "CONSTRUCTION",
    "CONSUMER_ELECTRONICS",
    "CONSUMER_GOODS",
    "CONSUMER_SERVICES",
    "COSMETICS",
    "DAIRY",
    "DEFENSE_SPACE",
    "DESIGN",
    "EDUCATION_MANAGEMENT",
    "E_LEARNING",
    "ELECTRICAL_ELECTRONIC_MANUFACTURING",
    "ENTERTAINMENT",
    "ENVIRONMENTAL_SERVICES",
    "EVENTS_SERVICES",
    "EXECUTIVE_OFFICE",
    "FACILITIES_SERVICES",
    "FARMING",
    "FINANCIAL_SERVICES",
    "FINE_ART",
    "FISHERY",
    "FOOD_BEVERAGES",
    "FOOD_PRODUCTION",
    "FUND_RAISING",
    "FURNITURE",
    "GAMBLING_CASINOS",
    "GLASS_CERAMICS_CONCRETE",
    "GOVERNMENT_ADMINISTRATION",
    "GOVERNMENT_RELATIONS",
    "GRAPHIC_DESIGN",
    "HEALTH_WELLNESS_AND_FITNESS",
    "HIGHER_EDUCATION",
    "HOSPITAL_HEALTH_CARE",
    "HOSPITALITY",
    "HUMAN_RESOURCES",
    "IMPORT_AND_EXPORT",
    "INDIVIDUAL_FAMILY_SERVICES",
    "INDUSTRIAL_AUTOMATION",
    "INFORMATION_SERVICES",
    "INFORMATION_TECHNOLOGY_AND_SERVICES",
    "INSURANCE",
    "INTERNATIONAL_AFFAIRS",
    "INTERNATIONAL_TRADE_AND_DEVELOPMENT",
    "INVESTMENT_BANKING",
    "INVESTMENT_MANAGEMENT",
    "JUDICIARY",
    "LAW_ENFORCEMENT",
    "LAW_PRACTICE",
    "LEGAL_SERVICES",
    "LEGISLATIVE_OFFICE",
    "LEISURE_TRAVEL_TOURISM",
    "LIBRARIES",
    "LOGISTICS_AND_SUPPLY_CHAIN",
    "LUXURY_GOODS_JEWELRY",
    "MACHINERY",
    "MANAGEMENT_CONSULTING",
    "MARITIME",
    "MARKET_RESEARCH",
    "MARKETING_AND_ADVERTISING",
    "MECHANICAL_OR_INDUSTRIAL_ENGINEERING",
    "MEDIA_PRODUCTION",
    "MEDICAL_DEVICES",
    "MEDICAL_PRACTICE",
    "MENTAL_HEALTH_CARE",
    "MILITARY",
    "MINING_METALS",
    "MOTION_PICTURES_AND_FILM",
    "MUSEUMS_AND_INSTITUTIONS",
    "MUSIC",
    "NANOTECHNOLOGY",
    "NEWSPAPERS",
    "NON_PROFIT_ORGANIZATION_MANAGEMENT",
    "OIL_ENERGY",
    "ONLINE_MEDIA",
    "OUTSOURCING_OFFSHORING",
    "PACKAGE_FREIGHT_DELIVERY",
    "PACKAGING_AND_CONTAINERS",
    "PAPER_FOREST_PRODUCTS",
    "PERFORMING_ARTS",
    "PHARMACEUTICALS",
    "PHILANTHROPY",
    "PHOTOGRAPHY",
    "PLASTICS",
    "POLITICAL_ORGANIZATION",
    "PRIMARY_SECONDARY_EDUCATION",
    "PRINTING",
    "PROFESSIONAL_TRAINING_COACHING",
    "PROGRAM_DEVELOPMENT",
    "PUBLIC_POLICY",
    "PUBLIC_RELATIONS_AND_COMMUNICATIONS",
    "PUBLIC_SAFETY",
    "PUBLISHING",
    "RAILROAD_MANUFACTURE",
    "RANCHING",
    "REAL_ESTATE",
    "RECREATIONAL_FACILITIES_AND_SERVICES",
    "RELIGIOUS_INSTITUTIONS",
    "RENEWABLES_ENVIRONMENT",
    "RESEARCH",
    "RESTAURANTS",
    "RETAIL",
    "SECURITY_AND_INVESTIGATIONS",
    "SEMICONDUCTORS",
    "SHIPBUILDING",
    "SPORTING_GOODS",
    "SPORTS",
    "STAFFING_AND_RECRUITING",
    "SUPERMARKETS",
    "TELECOMMUNICATIONS",
    "TEXTILES",
    "THINK_TANKS",
    "TOBACCO",
    "TRANSLATION_AND_LOCALIZATION",
    "TRANSPORTATION_TRUCKING_RAILROAD",
    "UTILITIES",
    "VENTURE_CAPITAL_PRIVATE_EQUITY",
    "VETERINARY",
    "WAREHOUSING",
    "WHOLESALE",
    "WINE_AND_SPIRITS",
    "WIRELESS",
    "WRITING_AND_EDITING",
    "MOBILE_GAMES",
}


def _normalize_industry(industry: str) -> Optional[str]:
    if not industry:
        return None

    normalized = industry.strip().upper().replace(" ", "_").replace("&", "AND").replace("-", "_")
    if normalized in HUBSPOT_INDUSTRIES:
        return normalized

    for hubspot_industry in HUBSPOT_INDUSTRIES:
        if normalized in hubspot_industry or hubspot_industry in normalized:
            return hubspot_industry

    return None


def _build_hubspot_client(access_token: str) -> Any:
    from hubspot import HubSpot

    return HubSpot(access_token=access_token)


def _create_contact_input(properties: dict[str, str], create: bool) -> Any:
    if create:
        from hubspot.crm.contacts import SimplePublicObjectInputForCreate

        return SimplePublicObjectInputForCreate(properties=properties)

    from hubspot.crm.contacts import SimplePublicObjectInput

    return SimplePublicObjectInput(properties=properties)


def _create_company_input(properties: dict[str, str], create: bool) -> Any:
    if create:
        from hubspot.crm.companies import SimplePublicObjectInputForCreate

        return SimplePublicObjectInputForCreate(properties=properties)

    from hubspot.crm.companies import SimplePublicObjectInput

    return SimplePublicObjectInput(properties=properties)


class HubSpotCrmSink(LeadSink):
    name = "hubspot"

    def __init__(
        self,
        access_token: str,
        config: HubSpotSinkConfig | dict | None = None,
        client: Any | None = None,
        workflow_client: HubSpotWorkflowClient | None = None,
    ) -> None:
        if not access_token and client is None:
            raise ValueError("HubSpot access token is required")

        if isinstance(config, HubSpotSinkConfig):
            self.config = config.model_dump()
        else:
            self.config = dict(config or {})

        self.client = client or _build_hubspot_client(access_token)
        self.workflow_client = workflow_client or HubSpotWorkflowClient(
            client=self.client,
            config=self.config.get("workflow", {}),
        )
        self._ensure_custom_properties()

    def write(
        self,
        leads: list[tuple[Contact, Optional[Company]]],
        context: Optional[dict] = None,
    ) -> dict:
        results = {
            "sink": self.name,
            "contacts_synced": 0,
            "contacts_failed": 0,
            "companies_synced": 0,
            "companies_failed": 0,
            "associations_created": 0,
            "workflow_enrolled": 0,
            "workflow_failed": 0,
        }

        for contact, company in leads:
            company_id = None
            if company and self.config.get("create_companies", True):
                company_id = self.sync_company(company)
                if company_id:
                    results["companies_synced"] += 1
                else:
                    results["companies_failed"] += 1

            contact_id = None
            if self.config.get("create_contacts", True):
                contact_id = self.sync_contact(contact, company_id)
                if contact_id:
                    results["contacts_synced"] += 1
                    if company_id:
                        results["associations_created"] += 1
                else:
                    results["contacts_failed"] += 1

            if self.workflow_client.should_enroll(contact):
                if self.workflow_client.enroll(contact):
                    results["workflow_enrolled"] += 1
                else:
                    results["workflow_failed"] += 1

            if contact_id:
                contact.external_ids["hubspot_contact_id"] = contact_id

        return results

    def _ensure_custom_properties(self) -> None:
        contact_properties = self.config.get("custom_properties", {}).get("contact", [])
        company_properties = self.config.get("custom_properties", {}).get("company", [])

        contact_property_definitions = {
            "enrichment_score": {
                "name": "enrichment_score",
                "label": "Enrichment Score",
                "type": "number",
                "field_type": "number",
                "group_name": "contactinformation",
                "description": "Lead score from enrichment system (0-100)",
            },
            "enrichment_segment": {
                "name": "enrichment_segment",
                "label": "Enrichment Segment",
                "type": "enumeration",
                "field_type": "select",
                "group_name": "contactinformation",
                "description": "Lead segment from enrichment",
                "options": [
                    {"label": "High Touch", "value": "high_touch"},
                    {"label": "Standard", "value": "standard"},
                    {"label": "Nurture", "value": "nurture"},
                ],
            },
            "enrichment_source": {
                "name": "enrichment_source",
                "label": "Enrichment Source",
                "type": "string",
                "field_type": "text",
                "group_name": "contactinformation",
                "description": "Data providers used for enrichment",
            },
            "ai_icebreaker": {
                "name": "ai_icebreaker",
                "label": "AI Icebreaker",
                "type": "string",
                "field_type": "textarea",
                "group_name": "contactinformation",
                "description": "AI-generated personalized icebreaker",
            },
            "persona_segment": {
                "name": "persona_segment",
                "label": "Persona Segment",
                "type": "string",
                "field_type": "text",
                "group_name": "contactinformation",
                "description": "Auto-assigned persona cluster",
            },
            "verified_email": {
                "name": "verified_email",
                "label": "Email Verified",
                "type": "enumeration",
                "field_type": "select",
                "group_name": "contactinformation",
                "description": "Email verification status",
                "options": [
                    {"label": "Valid", "value": "valid"},
                    {"label": "Invalid", "value": "invalid"},
                    {"label": "Catch All", "value": "catch_all"},
                    {"label": "Unknown", "value": "unknown"},
                    {"label": "Unverified", "value": "unverified"},
                ],
            },
            "email_sequence_ready": {
                "name": "email_sequence_ready",
                "label": "Email Sequence Ready",
                "type": "enumeration",
                "field_type": "booleancheckbox",
                "group_name": "contactinformation",
                "description": "Set to true when AI email sequence content is staged",
                "options": [
                    {"label": "Yes", "value": "true"},
                    {"label": "No", "value": "false"},
                ],
            },
        }
        for step in range(1, 6):
            contact_property_definitions[f"email_step_{step}_subject"] = {
                "name": f"email_step_{step}_subject",
                "label": f"Email Step {step} Subject",
                "type": "string",
                "field_type": "text",
                "group_name": "contactinformation",
                "description": f"AI-generated subject line for email step {step}",
            }
            contact_property_definitions[f"email_step_{step}_body"] = {
                "name": f"email_step_{step}_body",
                "label": f"Email Step {step} Body",
                "type": "string",
                "field_type": "textarea",
                "group_name": "contactinformation",
                "description": f"AI-generated email body for step {step}",
            }

        company_property_definitions = {
            "enrichment_source": {
                "name": "enrichment_source",
                "label": "Enrichment Source",
                "type": "string",
                "field_type": "text",
                "group_name": "companyinformation",
                "description": "Data providers used for enrichment",
            },
            "tech_stack": {
                "name": "tech_stack",
                "label": "Tech Stack",
                "type": "string",
                "field_type": "textarea",
                "group_name": "companyinformation",
                "description": "Technologies used by the company",
            },
            "funding_stage": {
                "name": "funding_stage",
                "label": "Funding Stage",
                "type": "string",
                "field_type": "text",
                "group_name": "companyinformation",
                "description": "Latest funding round type",
            },
            "employee_count_range": {
                "name": "employee_count_range",
                "label": "Employee Count Range",
                "type": "string",
                "field_type": "text",
                "group_name": "companyinformation",
                "description": "Employee count range",
            },
            "website_context": {
                "name": "website_context",
                "label": "Website Research Context",
                "type": "string",
                "field_type": "textarea",
                "group_name": "companyinformation",
                "description": "Context extracted from the company website",
            },
        }

        for property_name in contact_properties:
            if property_name in contact_property_definitions:
                self._create_property_if_not_exists("contacts", contact_property_definitions[property_name])

        for property_name in company_properties:
            if property_name in company_property_definitions:
                self._create_property_if_not_exists("companies", company_property_definitions[property_name])

    def _create_property_if_not_exists(self, object_type: str, property_def: dict[str, Any]) -> None:
        try:
            self.client.crm.properties.core_api.get_by_name(
                object_type=object_type,
                property_name=property_def["name"],
            )
            return
        except Exception:
            pass

        try:
            from hubspot.crm.properties import PropertyCreate

            property_create = PropertyCreate(**property_def)
            self.client.crm.properties.core_api.create(
                object_type=object_type,
                property_create=property_create,
            )
        except Exception:
            return

    def sync_contact(self, contact: Contact, company_id: Optional[str] = None) -> Optional[str]:
        if not contact.email:
            return None

        properties = self._contact_to_properties(contact)
        try:
            existing_id = self._find_contact_by_email(contact.email)
            if existing_id:
                result = self.client.crm.contacts.basic_api.update(
                    contact_id=existing_id,
                    simple_public_object_input=_create_contact_input(properties, create=False),
                )
                contact_id = result.id
            else:
                result = self.client.crm.contacts.basic_api.create(
                    simple_public_object_input_for_create=_create_contact_input(properties, create=True),
                )
                contact_id = result.id

            if company_id:
                self._associate_contact_to_company(contact_id, company_id)
            return contact_id
        except Exception:
            return None

    def sync_company(self, company: Company) -> Optional[str]:
        if not company.domain:
            return None

        properties = self._company_to_properties(company)
        try:
            existing_id = self._find_company_by_domain(company.domain)
            if existing_id:
                result = self.client.crm.companies.basic_api.update(
                    company_id=existing_id,
                    simple_public_object_input=_create_company_input(properties, create=False),
                )
                return result.id

            result = self.client.crm.companies.basic_api.create(
                simple_public_object_input_for_create=_create_company_input(properties, create=True),
            )
            return result.id
        except Exception:
            return None

    def sync_lead(self, contact: Contact, company: Optional[Company] = None) -> tuple[Optional[str], Optional[str]]:
        company_id = self.sync_company(company) if company else None
        contact_id = self.sync_contact(contact, company_id)
        return contact_id, company_id

    def _contact_to_properties(self, contact: Contact) -> dict[str, str]:
        props: dict[str, str] = {}

        if contact.email:
            props["email"] = contact.email
        if contact.first_name:
            props["firstname"] = contact.first_name
        if contact.last_name:
            props["lastname"] = contact.last_name
        if contact.phone:
            props["phone"] = contact.phone
        if contact.mobile:
            props["mobilephone"] = contact.mobile
        if contact.title:
            props["jobtitle"] = contact.title
        if contact.city:
            props["city"] = contact.city
        if contact.state:
            props["state"] = contact.state
        if contact.country:
            props["country"] = contact.country

        owner_id = self.config.get("default_owner_id")
        if owner_id:
            props["hubspot_owner_id"] = owner_id

        props["enrichment_score"] = str(int(contact.total_score))
        props["enrichment_segment"] = contact.segment.value
        props["enrichment_source"] = ", ".join(contact.enrichment_sources)
        if contact.persona:
            props["persona_segment"] = contact.persona
        if contact.ai_icebreaker:
            props["ai_icebreaker"] = contact.ai_icebreaker
        if contact.linkedin_url:
            props["hs_linkedin_url"] = contact.linkedin_url
        if contact.email_verification_status:
            props["verified_email"] = contact.email_verification_status.value

        if contact.ai_email_variants:
            has_content = False
            for step_data in parse_email_steps(contact.ai_email_variants):
                step = step_data.get("step")
                if not isinstance(step, int) or step < 1 or step > 5:
                    continue
                subject = step_data.get("subject", "")
                body = step_data.get("body", "")
                if subject:
                    props[f"email_step_{step}_subject"] = subject
                if body:
                    props[f"email_step_{step}_body"] = body[:65535]
                    has_content = True
            if has_content:
                props["email_sequence_ready"] = "true"

        return props

    def _company_to_properties(self, company: Company) -> dict[str, str]:
        props: dict[str, str] = {}

        if company.name:
            props["name"] = company.name
        if company.domain:
            props["domain"] = company.domain
        if company.industry:
            mapped_industry = _normalize_industry(company.industry)
            if mapped_industry:
                props["industry"] = mapped_industry
        if company.description:
            props["description"] = company.description[:65535]
        if company.employee_count:
            props["numberofemployees"] = str(company.employee_count)
        if company.revenue:
            props["annualrevenue"] = str(int(company.revenue))
        if company.headquarters_city:
            props["city"] = company.headquarters_city
        if company.headquarters_state:
            props["state"] = company.headquarters_state
        if company.headquarters_country:
            props["country"] = company.headquarters_country
        if company.linkedin_url:
            props["linkedin_company_page"] = company.linkedin_url
        if company.founded_year:
            props["founded_year"] = str(company.founded_year)

        props["enrichment_source"] = ", ".join(company.enrichment_sources)
        if company.tech_stack:
            props["tech_stack"] = ", ".join(company.tech_stack[:50])
        if company.funding and company.funding.last_round_type:
            props["funding_stage"] = company.funding.last_round_type
        if company.employee_range:
            props["employee_count_range"] = company.employee_range
        if company.website_context:
            props["website_context"] = company.website_context[:65535]

        return props

    def _find_contact_by_email(self, email: str) -> Optional[str]:
        try:
            from hubspot.crm.contacts import Filter, FilterGroup, PublicObjectSearchRequest

            search_request = PublicObjectSearchRequest(
                filter_groups=[FilterGroup(filters=[Filter(property_name="email", operator="EQ", value=email)])],
                limit=1,
            )
            result = self.client.crm.contacts.search_api.do_search(
                public_object_search_request=search_request,
            )
        except Exception:
            return None

        if result.results:
            return result.results[0].id
        return None

    def _find_company_by_domain(self, domain: str) -> Optional[str]:
        try:
            from hubspot.crm.companies import Filter, FilterGroup, PublicObjectSearchRequest

            search_request = PublicObjectSearchRequest(
                filter_groups=[FilterGroup(filters=[Filter(property_name="domain", operator="EQ", value=domain)])],
                limit=1,
            )
            result = self.client.crm.companies.search_api.do_search(
                public_object_search_request=search_request,
            )
        except Exception:
            return None

        if result.results:
            return result.results[0].id
        return None

    def _associate_contact_to_company(self, contact_id: str, company_id: str) -> bool:
        try:
            self.client.crm.contacts.associations_api.create(
                contact_id=contact_id,
                to_object_type="companies",
                to_object_id=company_id,
                association_type="contact_to_company",
            )
            return True
        except Exception:
            return False
