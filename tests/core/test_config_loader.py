from pathlib import Path

from open_waterfall.core.config.loader import load_config


def test_load_config_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("providers:\n  company_waterfall: []\n  contact_waterfall: []\n")

    config = load_config(str(config_path))

    assert config.providers.company_waterfall == []
    assert config.pipeline.merge_results is True
    assert config.sinks.enabled == ["csv"]

