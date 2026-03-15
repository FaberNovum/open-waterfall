from __future__ import annotations

from typing import Optional, Tuple

from open_waterfall.core.io.csv_output import export_contacts_to_csv
from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact
from open_waterfall.sinks.base import LeadSink


class CsvSink(LeadSink):
    name = "csv"

    def __init__(self, output_path: str):
        self.output_path = output_path

    def write(
        self,
        leads: list[Tuple[Contact, Optional[Company]]],
        context: Optional[dict] = None,
    ) -> dict:
        contacts = [contact for contact, _company in leads]
        companies = {
            company.domain: company
            for _contact, company in leads
            if company is not None
        }
        export_contacts_to_csv(contacts, companies, self.output_path)
        return {"sink": self.name, "rows_written": len(contacts), "output_path": self.output_path}
