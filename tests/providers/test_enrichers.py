from unittest.mock import patch

from open_waterfall.core.models.contact import EmailVerificationStatus
from open_waterfall.providers.apollo import ApolloEnricher
from open_waterfall.providers.hunter import HunterEnricher
from open_waterfall.providers.zerobounce import ZeroBounceEnricher


def test_apollo_enrich_company_success() -> None:
    enricher = ApolloEnricher(api_key="test_key")
    mock_response = {
        "organization": {
            "name": "Acme Inc",
            "primary_domain": "acme.com",
            "industry": "Technology",
            "estimated_num_employees": 500,
            "annual_revenue": 50_000_000,
            "city": "San Francisco",
            "state": "CA",
            "country": "United States",
            "technologies": ["Salesforce", "HubSpot"],
        }
    }

    with patch.object(enricher, "_make_request", return_value=mock_response):
        result = enricher.enrich_company("acme.com")

    assert result.success is True
    assert result.company is not None
    assert result.company.name == "Acme Inc"
    assert result.company.domain == "acme.com"


def test_hunter_enrich_contact_success() -> None:
    enricher = HunterEnricher(api_key="test_key")
    mock_response = {
        "data": {
            "email": "john@acme.com",
            "position": "Sales Manager",
            "sources": [{"uri": "https://linkedin.com/in/johndoe"}],
        }
    }

    with patch.object(enricher, "_make_request", return_value=mock_response):
        result = enricher.enrich_contact("John", "Doe", "acme.com")

    assert result.success is True
    assert result.contact is not None
    assert result.contact.email == "john@acme.com"


def test_zerobounce_status_mapping() -> None:
    assert ZeroBounceEnricher.map_status_to_enum("valid") == EmailVerificationStatus.VALID
    assert ZeroBounceEnricher.map_status_to_enum("invalid") == EmailVerificationStatus.INVALID
    assert ZeroBounceEnricher.map_status_to_enum("catch-all") == EmailVerificationStatus.CATCH_ALL
