from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact


def export_contacts_to_csv(
    contacts: list[Contact],
    companies: Optional[dict[str, Company]],
    output_path: str,
) -> None:
    """Export contact-centric rows with optional company context."""
    rows = []
    companies = companies or {}

    for contact in contacts:
        company = companies.get(contact.company_domain or "")
        rows.append(
            {
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "company_name": contact.company_name,
                "domain": contact.company_domain,
                "email": contact.email,
                "title": contact.title,
                "icp_score": contact.icp_score,
                "intent_score": contact.intent_score,
                "total_score": contact.total_score,
                "segment": contact.segment.value,
                "persona": contact.persona,
                "ai_summary": contact.ai_summary,
                "ai_icebreaker": contact.ai_icebreaker,
                "ai_email_variants": "\n\n===\n\n".join(contact.ai_email_variants),
                "ai_linkedin_message": contact.ai_linkedin_message,
                "company_industry": company.industry if company else None,
                "company_employee_count": company.employee_count if company else None,
                "company_revenue": company.revenue if company else None,
                "website_context": company.website_context if company else None,
            }
        )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, index=False)
