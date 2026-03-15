from __future__ import annotations

from typing import Optional

from open_waterfall.core.models.contact import Contact


class PersonaClassifier:
    """Keyword-based persona classifier driven by profile rules."""

    def __init__(self, persona_rules: Optional[dict] = None):
        self.persona_rules = persona_rules or {}

    def assign(self, contact: Contact) -> str:
        title = (contact.title or "").lower()
        department = (contact.department or "").lower()

        best_persona = "other"
        best_score = 0

        for persona_key, persona_def in self.persona_rules.items():
            score = 0
            for keyword in persona_def.get("title_keywords", []):
                if keyword.lower() in title:
                    score += 1
            for keyword in persona_def.get("department_keywords", []):
                if keyword.lower() in department:
                    score += 1
            if score > best_score:
                best_score = score
                best_persona = persona_key

        contact.persona = best_persona
        return best_persona
