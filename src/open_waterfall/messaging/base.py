from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact


class MessageStrategy(ABC):
    name: str = "base"

    @abstractmethod
    def generate(
        self,
        contact: Contact,
        company: Optional[Company] = None,
        context: Optional[dict] = None,
    ) -> Contact:
        """Return a mutated contact with messaging outputs."""
