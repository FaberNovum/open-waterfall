from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class APICallRecord(BaseModel):
    provider: str
    endpoint: str
    success: bool
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


DEFAULT_COSTS: dict[str, float] = {
    "apollo": 0.03,
    "clearbit": 0.10,
    "hunter": 0.01,
    "zerobounce": 0.007,
    "openai": 0.02,
    "hubspot": 0.0,
}


class CostTracker:
    """Tracks successful API calls and rough estimated cost."""

    def __init__(self, cost_overrides: Optional[dict] = None) -> None:
        self.costs = {**DEFAULT_COSTS}
        if cost_overrides:
            self.costs.update(cost_overrides)
        self.records: list[APICallRecord] = []

    def record(
        self,
        provider: str,
        endpoint: str,
        success: bool = True,
        error: Optional[str] = None,
        tokens_used: Optional[int] = None,
    ) -> None:
        self.records.append(
            APICallRecord(
                provider=provider,
                endpoint=endpoint,
                success=success,
                error=error,
                tokens_used=tokens_used,
            )
        )

    def total_estimated_cost(self) -> float:
        return sum(self.costs.get(rec.provider, 0.0) for rec in self.records if rec.success)
