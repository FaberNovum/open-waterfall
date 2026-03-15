from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import pytest

pytest.importorskip("hubspot")

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact, EmailVerificationStatus, Segment
from open_waterfall.sinks.hubspot import HubSpotCrmSink, HubSpotDeduper, HubSpotWorkflowClient


@dataclass
class FakeResult:
    id: str
    properties: dict[str, Any]


class FakeSearchResponse:
    def __init__(self, results: list[FakeResult]):
        self.results = results


class FakeAssociationsResponse:
    def __init__(self, company_ids: list[str]):
        self.results = [type("Association", (), {"id": company_id})() for company_id in company_ids]


class FakeContactsSearchApi:
    def __init__(self, client: "FakeHubSpotClient") -> None:
        self.client = client

    def do_search(self, public_object_search_request: Any) -> FakeSearchResponse:
        filter_groups = getattr(public_object_search_request, "filter_groups", []) or []
        results: list[FakeResult] = []
        for filter_group in filter_groups:
            filters = {filter_.property_name: filter_.value for filter_ in getattr(filter_group, "filters", [])}
            if "email" in filters:
                for contact_id, payload in self.client.contacts.items():
                    if payload["properties"].get("email", "").lower() == str(filters["email"]).lower():
                        results.append(FakeResult(contact_id, payload["properties"]))
            elif {"firstname", "lastname"} <= filters.keys():
                for contact_id, payload in self.client.contacts.items():
                    properties = payload["properties"]
                    if (
                        properties.get("firstname") == filters["firstname"]
                        and properties.get("lastname") == filters["lastname"]
                    ):
                        results.append(FakeResult(contact_id, properties))
        return FakeSearchResponse(results)


class FakeCompaniesSearchApi:
    def __init__(self, client: "FakeHubSpotClient") -> None:
        self.client = client

    def do_search(self, public_object_search_request: Any) -> FakeSearchResponse:
        filter_groups = getattr(public_object_search_request, "filter_groups", []) or []
        results: list[FakeResult] = []
        for filter_group in filter_groups:
            filters = {filter_.property_name: filter_.value for filter_ in getattr(filter_group, "filters", [])}
            domain = str(filters.get("domain", "")).lower()
            if not domain:
                continue
            for company_id, payload in self.client.companies.items():
                if payload["properties"].get("domain", "").lower() == domain:
                    results.append(FakeResult(company_id, payload["properties"]))
        return FakeSearchResponse(results)


class FakeContactsBasicApi:
    def __init__(self, client: "FakeHubSpotClient") -> None:
        self.client = client

    def create(self, simple_public_object_input_for_create: Any) -> FakeResult:
        return self.client.create_contact(simple_public_object_input_for_create.properties)

    def update(self, contact_id: str, simple_public_object_input: Any) -> FakeResult:
        return self.client.update_contact(contact_id, simple_public_object_input.properties)


class FakeCompaniesBasicApi:
    def __init__(self, client: "FakeHubSpotClient") -> None:
        self.client = client

    def create(self, simple_public_object_input_for_create: Any) -> FakeResult:
        return self.client.create_company(simple_public_object_input_for_create.properties)

    def update(self, company_id: str, simple_public_object_input: Any) -> FakeResult:
        return self.client.update_company(company_id, simple_public_object_input.properties)

    def get_by_id(self, company_id: str, properties: list[str] | None = None) -> FakeResult:
        company = self.client.companies[company_id]
        return FakeResult(company_id, company["properties"])


class FakeContactsAssociationsApi:
    def __init__(self, client: "FakeHubSpotClient") -> None:
        self.client = client

    def create(self, contact_id: str, to_object_type: str, to_object_id: str, association_type: str) -> None:
        self.client.contact_company_links.setdefault(contact_id, set()).add(to_object_id)

    def get_all(self, contact_id: str, to_object_type: str) -> FakeAssociationsResponse:
        return FakeAssociationsResponse(sorted(self.client.contact_company_links.get(contact_id, set())))


class FakePropertiesCoreApi:
    def __init__(self) -> None:
        self.created: dict[str, set[str]] = {"contacts": set(), "companies": set()}

    def get_by_name(self, object_type: str, property_name: str) -> None:
        if property_name not in self.created[object_type]:
            raise RuntimeError("missing")

    def create(self, object_type: str, property_create: Any) -> None:
        self.created[object_type].add(property_create.name)


class FakeHubSpotClient:
    def __init__(self) -> None:
        self.contacts: dict[str, dict[str, Any]] = {}
        self.companies: dict[str, dict[str, Any]] = {}
        self.contact_company_links: dict[str, set[str]] = {}
        self.requests: list[dict[str, Any]] = []
        self._contact_index = 0
        self._company_index = 0
        self.crm = type(
            "CRM",
            (),
            {
                "contacts": type(
                    "Contacts",
                    (),
                    {
                        "search_api": FakeContactsSearchApi(self),
                        "basic_api": FakeContactsBasicApi(self),
                        "associations_api": FakeContactsAssociationsApi(self),
                    },
                )(),
                "companies": type(
                    "Companies",
                    (),
                    {
                        "search_api": FakeCompaniesSearchApi(self),
                        "basic_api": FakeCompaniesBasicApi(self),
                    },
                )(),
                "properties": type(
                    "Properties",
                    (),
                    {
                        "core_api": FakePropertiesCoreApi(),
                    },
                )(),
            },
        )()

    def create_contact(self, properties: dict[str, Any]) -> FakeResult:
        self._contact_index += 1
        contact_id = f"contact-{self._contact_index}"
        self.contacts[contact_id] = {"properties": dict(properties)}
        return FakeResult(contact_id, self.contacts[contact_id]["properties"])

    def update_contact(self, contact_id: str, properties: dict[str, Any]) -> FakeResult:
        self.contacts[contact_id]["properties"].update(properties)
        return FakeResult(contact_id, self.contacts[contact_id]["properties"])

    def create_company(self, properties: dict[str, Any]) -> FakeResult:
        self._company_index += 1
        company_id = f"company-{self._company_index}"
        self.companies[company_id] = {"properties": dict(properties)}
        return FakeResult(company_id, self.companies[company_id]["properties"])

    def update_company(self, company_id: str, properties: dict[str, Any]) -> FakeResult:
        self.companies[company_id]["properties"].update(properties)
        return FakeResult(company_id, self.companies[company_id]["properties"])

    def api_request(self, request: dict[str, Any]) -> Any:
        self.requests.append(request)
        return type("Response", (), {"status_code": 204})()


def test_hubspot_crm_sink_syncs_leads_and_enrolls_workflow() -> None:
    client = FakeHubSpotClient()
    sink = HubSpotCrmSink(
        access_token="token",
        client=client,
        config={
            "create_contacts": True,
            "create_companies": True,
            "default_owner_id": "owner-123",
            "custom_properties": {
                "contact": ["enrichment_score", "email_step_1_subject", "email_step_1_body"],
                "company": ["tech_stack", "website_context"],
            },
            "workflow": {
                "auto_enroll": True,
                "min_score": 80,
                "require_verified_email": True,
                "default_workflow_id": "workflow-1",
            },
        },
    )
    contact = Contact(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        title="VP Sales",
        total_score=92,
        segment=Segment.HIGH_TOUCH,
        persona="sales",
        ai_icebreaker="Saw your recent launch.",
        ai_email_variants=[
            "STEP: 1\nSUBJECT: First touch\nTHREAD: new\nSEND: Day 0\n---\nBody copy\n---",
        ],
        email_verification_status=EmailVerificationStatus.VALID,
        enrichment_sources=["apollo", "website"],
        company_domain="example.com",
        company_name="Example Co",
    )
    company = Company(
        domain="example.com",
        name="Example Co",
        industry="Computer Software",
        website_context="Expanding into healthcare.",
        tech_stack=["HubSpot", "Salesforce"],
    )

    result = sink.write([(contact, company)])

    assert result["contacts_synced"] == 1
    assert result["companies_synced"] == 1
    assert result["workflow_enrolled"] == 1
    assert contact.external_ids["hubspot_contact_id"] == "contact-1"
    assert client.contacts["contact-1"]["properties"]["email_step_1_subject"] == "First touch"
    assert client.contacts["contact-1"]["properties"]["email_sequence_ready"] == "true"
    assert client.companies["company-1"]["properties"]["industry"] == "COMPUTER_SOFTWARE"
    assert client.requests[0]["path"] == "/automation/v2/workflows/workflow-1/enrollments/contacts/jane@example.com"


def test_hubspot_workflow_client_respects_thresholds() -> None:
    workflow = HubSpotWorkflowClient(
        client=FakeHubSpotClient(),
        config={
            "auto_enroll": True,
            "min_score": 80,
            "require_verified_email": True,
            "default_workflow_id": "wf-1",
        },
    )
    contact = Contact(
        email="jane@example.com",
        total_score=75,
        email_verification_status=EmailVerificationStatus.VALID,
    )

    assert workflow.should_enroll(contact) is False


def test_hubspot_deduper_filters_existing_email_and_domain_matches() -> None:
    client = FakeHubSpotClient()
    existing_company = client.create_company({"domain": "example.com"})
    existing_contact = client.create_contact(
        {"email": "jane@example.com", "firstname": "Jane", "lastname": "Doe"},
    )
    client.contact_company_links[existing_contact.id] = {existing_company.id}
    deduper = HubSpotDeduper(client)
    df = pd.DataFrame(
        [
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@example.com",
                "domain": "example.com",
            },
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "",
                "domain": "example.com",
            },
            {
                "first_name": "Net",
                "last_name": "New",
                "email": "new@example.com",
                "domain": "example.org",
            },
        ]
    )

    filtered, stats = deduper.deduplicate_leads(df)

    assert len(filtered) == 1
    assert filtered.iloc[0]["email"] == "new@example.com"
    assert stats["duplicates_by_email"] == 1
    assert stats["duplicates_by_name"] == 1
