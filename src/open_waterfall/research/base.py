from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact


class ResearchModule(ABC):
    name: str = "base"

    @abstractmethod
    def run(
        self,
        contact: Contact,
        company: Optional[Company] = None,
        context: Optional[dict] = None,
    ) -> Contact:
        """Return a mutated contact with added research context."""
