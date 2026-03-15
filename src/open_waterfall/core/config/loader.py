from __future__ import annotations

import os
from pathlib import Path

import yaml

from open_waterfall.core.config.schema import OpenWaterfallConfig


def load_config(config_path: str) -> OpenWaterfallConfig:
    """Load config with basic `${ENV}` substitution."""
    config_str = Path(config_path).read_text()
    for key, value in os.environ.items():
        config_str = config_str.replace(f"${{{key}}}", value)
    raw = yaml.safe_load(config_str) or {}
    return OpenWaterfallConfig.model_validate(raw)

