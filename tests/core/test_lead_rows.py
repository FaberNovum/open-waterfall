import pandas as pd

from open_waterfall.core.io.lead_rows import dataframe_to_lead_pairs


def test_dataframe_to_lead_pairs_maps_contact_and_company() -> None:
    df = pd.DataFrame(
        [
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "domain": "example.com",
                "company_name": "Example",
                "company_industry": "SaaS",
                "employee_count": 250,
            }
        ]
    )

    lead_pairs = dataframe_to_lead_pairs(df)

    contact, company = lead_pairs[0]
    assert contact.first_name == "Jane"
    assert company is not None
    assert company.domain == "example.com"
    assert company.industry == "SaaS"


def test_dataframe_to_lead_pairs_restores_ai_email_variants() -> None:
    df = pd.DataFrame(
        [
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "domain": "example.com",
                "company_name": "Example",
                "ai_email_variants": (
                    "STEP: 1\nSUBJECT: First\nTHREAD: new\nSEND: Day 0\n---\nBody 1\n---\n\n===\n\n"
                    "STEP: 2\nSUBJECT: Second\nTHREAD: reply\nSEND: Day 2\n---\nBody 2\n---"
                ),
                "verified_email": "valid",
                "enrichment_sources": "apollo, website",
            }
        ]
    )

    lead_pairs = dataframe_to_lead_pairs(df)

    contact, _company = lead_pairs[0]
    assert len(contact.ai_email_variants) == 2
    assert contact.email_verification_status.value == "valid"
    assert contact.enrichment_sources == ["apollo", "website"]
