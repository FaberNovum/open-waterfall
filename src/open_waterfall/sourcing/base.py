from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from open_waterfall.core.config.schema import SourceConfig
from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact


class BaseLeadSource(ABC):
    """Abstract lead source interface."""

    name: str = "base"

    @abstractmethod
    def search(self, config: SourceConfig) -> list[tuple[Contact, Optional[Company]]]:
        """Return lead pairs sourced from an external provider."""
