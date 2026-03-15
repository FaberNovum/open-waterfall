from __future__ import annotations

from pydantic import BaseModel, Field


class PipelineBatchResult(BaseModel):
    """Minimal batch summary for CLI output."""

    input_rows: int = 0
    output_rows: int = 0
    warnings: list[str] = Field(default_factory=list)

