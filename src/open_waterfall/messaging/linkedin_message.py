from __future__ import annotations

from typing import Optional

from openai import OpenAI

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact
from open_waterfall.messaging.base import MessageStrategy


class LinkedInMessageStrategy(MessageStrategy):
    name = "linkedin_message"

    def __init__(self, api_key: str = "", model: str = "gpt-4.1", temperature: float = 0.7):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.client = OpenAI(api_key=api_key) if api_key else None

    def generate(
        self,
        contact: Contact,
        company: Optional[Company] = None,
        context: Optional[dict] = None,
    ) -> Contact:
        if self.client:
            generated = self._generate_with_ai(contact, company)
            if generated:
                contact.ai_linkedin_message = generated
                return contact

        company_name = company.name if company else contact.company_name or "your company"
        contact.ai_linkedin_message = (
            f"Hi {contact.first_name or ''}, I wanted to connect after seeing your work at {company_name}."
        ).strip()
        return contact

    def _generate_with_ai(self, contact: Contact, company: Optional[Company]) -> str:
        try:
            prospect_name = contact.full_name or " ".join(
                filter(None, [contact.first_name or "", contact.last_name or ""])
            ).strip()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Write a genuine LinkedIn connection request under 280 characters. No sales pitch.",
                    },
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                f"Name: {prospect_name}",
                                f"Title: {contact.title or ''}",
                                f"Company: {company.name if company else contact.company_name or ''}",
                                f"Icebreaker: {contact.ai_icebreaker or ''}",
                                f"Context: {contact.ai_summary or contact.linkedin_context or ''}",
                            ]
                        ),
                    },
                ],
                max_tokens=120,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()[:280]
        except Exception:
            return ""
