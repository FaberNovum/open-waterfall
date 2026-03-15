from __future__ import annotations

from typing import Optional

from openai import OpenAI

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact
from open_waterfall.messaging.base import MessageStrategy


class ColdEmailSequenceStrategy(MessageStrategy):
    """Generate cold email sequences with optional AI backing."""

    name = "cold_email_sequence"

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
        context = context or {}
        if self.client:
            generated = self._generate_with_ai(contact, company, context)
            if generated:
                contact.ai_email_variants = generated
                return contact

        sender = context.get("sender_name", "Example Sender")
        sender_company = context.get("sender_company", "Example Company")
        company_name = company.name if company else contact.company_name or "your company"
        title = contact.title or "your workflow"
        contact.ai_email_variants = [
            "\n".join(
                [
                    "STEP: 1",
                    "SEND: Day 0",
                    f"SUBJECT: thought on {company_name}",
                    "THREAD: new",
                    "---",
                    f"{contact.first_name or 'Hi'}, I had one thought about how {company_name} might handle {title.lower()}. Worth exploring?\n\n— {sender}\n{sender_company}",
                    "---",
                ]
            ),
            "\n".join(
                [
                    "STEP: 2",
                    "SEND: Day 3",
                    "SUBJECT: quick follow-up",
                    "THREAD: reply-to-1",
                    "---",
                    f"{contact.first_name or 'Hi'} - should I close the loop here?\n\n— {sender}",
                    "---",
                ]
            ),
        ]
        return contact

    def _generate_with_ai(
        self,
        contact: Contact,
        company: Optional[Company],
        context: dict,
    ) -> list[str]:
        try:
            company_name = company.name if company else contact.company_name or "their company"
            prospect_name = contact.full_name or " ".join(
                filter(None, [contact.first_name or "", contact.last_name or ""])
            ).strip()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You write concise, specific B2B outbound emails. Return only structured sequence output.",
                    },
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                "Generate a 5-step cold email sequence.",
                                "Return each email in this exact format:",
                                "STEP: <n>",
                                "SEND: Day <n>",
                                "SUBJECT: <text>",
                                "THREAD: <new|reply-to-1|reply-to-4>",
                                "---",
                                "<body>",
                                "---",
                                "===",
                                f"Prospect: {prospect_name}",
                                f"Title: {contact.title or ''}",
                                f"Company: {company_name}",
                                f"Industry: {company.industry if company else ''}",
                                f"Persona: {contact.persona or ''}",
                                f"Summary: {contact.ai_summary or ''}",
                                f"Icebreaker: {contact.ai_icebreaker or ''}",
                                f"Triggers: {', '.join(contact.trigger_events)}",
                                f"Value prop: {context.get('value_prop', '')}",
                                f"Sender: {context.get('sender_name', 'Example Sender')} at {context.get('sender_company', 'Example Company')}",
                                "Keep the emails plain text, concise, and question-led.",
                            ]
                        ),
                    },
                ],
                max_tokens=1800,
                temperature=self.temperature,
            )
            content = response.choices[0].message.content.strip()
            return [item.strip() for item in content.split("===") if "STEP:" in item and "SUBJECT:" in item]
        except Exception:
            return []
