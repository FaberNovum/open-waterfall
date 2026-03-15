from __future__ import annotations

from typing import Optional

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact
from open_waterfall.research.base import ResearchModule


class WebsiteContextResearch(ResearchModule):
    name = "website_context"

    def run(
        self,
        contact: Contact,
        company: Optional[Company] = None,
        context: Optional[dict] = None,
    ) -> Contact:
        if company and company.website_context and not contact.ai_icebreaker:
            contact.ai_icebreaker = company.website_context.split(".")[0]
        return contact
