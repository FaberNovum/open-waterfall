from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact


class CheckpointData(BaseModel):
    last_processed_index: int = -1
    processed_indices: list[int] = Field(default_factory=list)
    contacts: list[Contact] = Field(default_factory=list)
    companies: dict[str, Company] = Field(default_factory=dict)
    cost_tracker_state: Optional[dict] = None
    input_file: str = ""
    config_hash: str = ""
    total_rows: int = 0
    cli_flags: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CheckpointManager:
    """Atomic save/load of pipeline checkpoint files."""

    def __init__(self, checkpoint_path: str) -> None:
        self.path = Path(checkpoint_path)

    def save(self, data: CheckpointData) -> None:
        data.updated_at = datetime.utcnow()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(data.model_dump_json(indent=2))
        os.replace(tmp_path, self.path)

    def load(self) -> CheckpointData:
        return CheckpointData.model_validate_json(self.path.read_text())

    def exists(self) -> bool:
        return self.path.exists()

    @staticmethod
    def compute_config_hash(config: dict, input_file: str) -> str:
        config_json = json.dumps(config, sort_keys=True)
        config_digest = hashlib.sha256(config_json.encode()).hexdigest()
        file_digest = hashlib.sha256(Path(input_file).read_bytes()).hexdigest()
        return hashlib.sha256((config_digest + file_digest).encode()).hexdigest()

