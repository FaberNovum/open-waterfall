from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact


class LeadSink(ABC):
    name: str = "base"

    @abstractmethod
    def write(
        self,
        leads: list[Tuple[Contact, Optional[Company]]],
        context: Optional[dict] = None,
    ) -> dict:
        """Persist enriched leads and return a summary."""
