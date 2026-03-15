from pathlib import Path

from open_waterfall.core.config.loader import load_config


def test_load_config_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("providers:\n  company_waterfall: []\n  contact_waterfall: []\n")

    config = load_config(str(config_path))

    assert config.providers.company_waterfall == []
    assert config.pipeline.merge_results is True
    assert config.sinks.enabled == ["csv"]


def test_load_config_preserves_scoring_icp(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "providers:",
                "  company_waterfall: []",
                "  contact_waterfall: []",
                "scoring:",
                "  icp:",
                "    industries: [SaaS]",
                "    min_revenue: 1000000",
            ]
        )
    )

    config = load_config(str(config_path))

    assert config.scoring.icp == {"industries": ["SaaS"], "min_revenue": 1000000}


def test_load_config_merges_shipped_profiles(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "profiles:",
                "  - generic_b2b",
                "  - outbound_csv",
                "providers:",
                "  company_waterfall: [demo]",
                "  contact_waterfall: [demo]",
            ]
        )
    )

    config = load_config(str(config_path))

    assert config.providers.company_waterfall == ["demo"]
    assert config.providers.contact_waterfall == ["demo"]
    assert config.pipeline.skip_research is False
    assert config.pipeline.skip_messaging is False
    assert config.messaging.enabled is True
    assert config.sinks.csv["output_path"] == "./output/outbound.csv"
    assert config.scoring.icp["industries"] == ["SaaS", "Technology", "Software"]


def test_load_config_reads_env_from_project_root(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / "project"
    config_dir = project_root / "examples" / "apollo"
    config_dir.mkdir(parents=True)
    (project_root / ".git").mkdir()
    (project_root / ".env").write_text("OW_TEST_APOLLO_API_KEY=from-dotenv\n")

    config_path = config_dir / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "providers:",
                "  company_waterfall: [apollo]",
                "  contact_waterfall: []",
                "  api_keys:",
                "    apollo: ${OW_TEST_APOLLO_API_KEY}",
            ]
        )
    )

    monkeypatch.chdir(project_root)
    monkeypatch.delenv("OW_TEST_APOLLO_API_KEY", raising=False)

    config = load_config(str(config_path))

    assert config.providers.api_keys["apollo"] == "from-dotenv"
