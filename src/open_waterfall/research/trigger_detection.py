from __future__ import annotations

from typing import Optional

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact
from open_waterfall.research.base import ResearchModule


class TriggerDetectionResearch(ResearchModule):
    name = "trigger_detection"

    def run(
        self,
        contact: Contact,
        company: Optional[Company] = None,
        context: Optional[dict] = None,
    ) -> Contact:
        if company and company.hiring and company.hiring.open_positions:
            contact.trigger_events.append(f"Open roles: {company.hiring.open_positions}")
        return contact
