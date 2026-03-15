from unittest.mock import patch

from open_waterfall.core.config.schema import SourceConfig, SourceFiltersConfig
from open_waterfall.providers.apollo import ApolloSearchResult
from open_waterfall.sourcing.apollo import ApolloLeadSource


def test_apollo_source_maps_people_to_lead_pairs_and_dedupes() -> None:
    source = ApolloLeadSource(api_key="test-key")
    search_result = ApolloSearchResult(
        people=[
            {
                "id": "person-1",
                "first_name": "Jane",
                "last_name": "Doe",
                "name": "Jane Doe",
                "title": "VP Sales",
                "email": "jane@example.com",
                "linkedin_url": "https://linkedin.com/in/janedoe",
                "organization": {
                    "name": "Example",
                    "primary_domain": "example.com",
                    "industry": "SaaS",
                    "estimated_num_employees": 200,
                },
            },
            {
                "id": "person-1-duplicate",
                "first_name": "Jane",
                "last_name": "Doe",
                "name": "Jane Doe",
                "title": "VP Sales",
                "email": "jane@example.com",
                "linkedin_url": "https://linkedin.com/in/janedoe",
                "organization": {
                    "name": "Example",
                    "primary_domain": "example.com",
                },
            },
        ],
        total_entries=2,
        page=1,
        per_page=25,
    )

    config = SourceConfig(
        enabled=True,
        provider="apollo",
        max_results=25,
        page_size=25,
        filters=SourceFiltersConfig(titles=["VP Sales"]),
    )

    with patch.object(source.enricher, "search_people", return_value=search_result):
        lead_pairs = source.search(config)

    assert len(lead_pairs) == 1
    contact, company = lead_pairs[0]
    assert contact.first_name == "Jane"
    assert contact.external_ids["apollo_person_id"] == "person-1"
    assert company is not None
    assert company.domain == "example.com"
    assert company.industry == "SaaS"
