from __future__ import annotations

from typing import Optional

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact
from open_waterfall.research.base import ResearchModule


class ContactSummaryResearch(ResearchModule):
    name = "contact_summary"

    def run(
        self,
        contact: Contact,
        company: Optional[Company] = None,
        context: Optional[dict] = None,
    ) -> Contact:
        if not contact.ai_summary and (contact.title or company):
            company_name = company.name if company else contact.company_name or "their company"
            role = contact.title or "professional"
            contact.ai_summary = f"{contact.first_name or 'This contact'} appears to be a {role} at {company_name}."
        return contact
