from pathlib import Path

from open_waterfall.core.io.csv_input import parse_input_csv
from open_waterfall.core.io.csv_output import export_contacts_to_csv
from open_waterfall.core.io.lead_rows import dataframe_to_lead_pairs
from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact


def test_csv_roundtrip_preserves_message_and_company_context(tmp_path: Path) -> None:
    contact = Contact(
        first_name="Jane",
        last_name="Doe",
        company_name="Example Co",
        company_domain="example.com",
        email="jane@example.com",
        title="VP Sales",
        ai_summary="Summary text",
        ai_icebreaker="Relevant opener",
        ai_email_variants=[
            "STEP: 1\nSUBJECT: First touch\nTHREAD: new\nSEND: Day 0\n---\nBody 1\n---",
            "STEP: 2\nSUBJECT: Follow up\nTHREAD: reply\nSEND: Day 2\n---\nBody 2\n---",
        ],
        persona="sales",
    )
    company = Company(
        domain="example.com",
        name="Example Co",
        industry="Software",
        employee_count=200,
        revenue=5_000_000,
        website_context="Expanding into new markets.",
    )
    output_path = tmp_path / "roundtrip.csv"

    export_contacts_to_csv([contact], {"example.com": company}, str(output_path))
    df = parse_input_csv(str(output_path))
    lead_pairs = dataframe_to_lead_pairs(df)

    restored_contact, restored_company = lead_pairs[0]
    assert restored_contact.email == "jane@example.com"
    assert restored_contact.ai_summary == "Summary text"
    assert restored_contact.ai_icebreaker == "Relevant opener"
    assert len(restored_contact.ai_email_variants) == 2
    assert restored_contact.persona == "sales"
    assert restored_company is not None
    assert restored_company.domain == "example.com"
    assert restored_company.website_context == "Expanding into new markets."
