from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from open_waterfall.cli.app import main
from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact
from open_waterfall.core.config.schema import OpenWaterfallConfig
from open_waterfall.sinks.bootstrap import build_sinks


def test_score_command_writes_output(tmp_path: Path) -> None:
    input_csv = tmp_path / "leads.csv"
    input_csv.write_text(
        "first_name,last_name,domain,company_name,industry,revenue,employee_count\n"
        "Jane,Doe,example.com,Example,SaaS,5000000,200\n"
    )

    output_csv = tmp_path / "scored.csv"
    config = tmp_path / "config.yaml"
    config.write_text(
        "\n".join(
            [
                "providers:",
                "  company_waterfall: []",
                "  contact_waterfall: []",
                "sinks:",
                "  enabled: [csv]",
                "  csv:",
                f"    output_path: {output_csv}",
            ]
        )
    )

    result = CliRunner().invoke(main, ["score", str(input_csv), "--config", str(config)])

    assert result.exit_code == 0
    assert output_csv.exists()


def test_message_command_writes_output(tmp_path: Path) -> None:
    input_csv = tmp_path / "leads.csv"
    input_csv.write_text("first_name,last_name,domain,company_name,title\nJane,Doe,example.com,Example,VP Sales\n")

    output_csv = tmp_path / "messages.csv"
    config = tmp_path / "config.yaml"
    config.write_text(
        "\n".join(
            [
                "providers:",
                "  company_waterfall: []",
                "  contact_waterfall: []",
                "research:",
                "  enabled_modules: [contact_summary, website_context]",
                "messaging:",
                "  enabled: true",
                "  strategy: cold_email_sequence",
                "  sender:",
                "    name: Sender",
                "    company: SenderCo",
                "  value_prop: Example value prop",
                "sinks:",
                "  enabled: [csv]",
                "  csv:",
                f"    output_path: {output_csv}",
            ]
        )
    )

    result = CliRunner().invoke(main, ["message", str(input_csv), "--config", str(config)])

    assert result.exit_code == 0
    assert output_csv.exists()


def test_sync_command_csv_sink(tmp_path: Path) -> None:
    input_csv = tmp_path / "leads.csv"
    input_csv.write_text("first_name,last_name,domain,company_name\nJane,Doe,example.com,Example\n")

    output_csv = tmp_path / "synced.csv"
    config = tmp_path / "config.yaml"
    config.write_text(
        "\n".join(
            [
                "providers:",
                "  company_waterfall: []",
                "  contact_waterfall: []",
                "sinks:",
                "  enabled: [csv]",
                "  csv:",
                f"    output_path: {output_csv}",
            ]
        )
    )

    result = CliRunner().invoke(main, ["sync", str(input_csv), "--config", str(config)])

    assert result.exit_code == 0
    assert output_csv.exists()


def test_search_command_writes_output(tmp_path: Path) -> None:
    output_csv = tmp_path / "sourced.csv"
    config = tmp_path / "config.yaml"
    config.write_text(
        "\n".join(
            [
                "providers:",
                "  company_waterfall: []",
                "  contact_waterfall: []",
                "source:",
                "  enabled: true",
                "  provider: apollo",
                "  max_results: 10",
                "sinks:",
                "  enabled: [csv]",
                "  csv:",
                f"    output_path: {output_csv}",
            ]
        )
    )

    class FakeLeadSource:
        name = "apollo"

        def search(self, _config: object) -> list[tuple[Contact, Company]]:
            return [
                (
                    Contact(first_name="Jane", last_name="Doe", company_domain="example.com", company_name="Example"),
                    Company(domain="example.com", name="Example", industry="SaaS", employee_count=200, revenue=5000000),
                )
            ]

    with patch("open_waterfall.cli.commands.search.build_lead_source", return_value=(FakeLeadSource(), [])):
        result = CliRunner().invoke(main, ["search", "--config", str(config)])

    assert result.exit_code == 0
    assert "sourced 1 leads from apollo" in result.output
    assert output_csv.exists()


def test_demo_command_runs_local_examples(tmp_path: Path) -> None:
    repo_root = tmp_path / "demo-repo"
    (repo_root / "examples" / "enrich_to_csv").mkdir(parents=True)
    (repo_root / "examples" / "outbound_to_csv").mkdir(parents=True)

    (repo_root / "examples" / "enrich_to_csv" / "leads.csv").write_text(
        "first_name,last_name,domain,company_name\nJane,Doe,example.com,Example\n"
    )
    (repo_root / "examples" / "enrich_to_csv" / "config.yaml").write_text(
        "providers:\n  company_waterfall: []\n  contact_waterfall: []\n"
        "sinks:\n  enabled: [csv]\n  csv:\n    output_path: ./output/enriched.csv\n"
    )
    (repo_root / "examples" / "outbound_to_csv" / "leads.csv").write_text(
        "first_name,last_name,domain,company_name\nJane,Doe,example.com,Example\n"
    )
    (repo_root / "examples" / "outbound_to_csv" / "config.yaml").write_text(
        "providers:\n  company_waterfall: []\n  contact_waterfall: []\n"
        "messaging:\n  enabled: true\n  strategy: cold_email_sequence\n"
        "sinks:\n  enabled: [csv]\n  csv:\n    output_path: ./output/outbound.csv\n"
    )

    runner = CliRunner()
    with patch("open_waterfall.cli.commands.demo._repo_root", return_value=repo_root):
        result = runner.invoke(main, ["demo"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Running local enrich walkthrough..." in result.output
    assert "Running local outbound walkthrough..." in result.output


def test_build_sinks_warns_when_hubspot_token_missing() -> None:
    config = OpenWaterfallConfig.model_validate(
        {
            "providers": {"company_waterfall": [], "contact_waterfall": []},
            "sinks": {
                "enabled": ["hubspot"],
                "hubspot": {"enabled": True},
            },
        }
    )

    sinks, warnings = build_sinks(config)

    assert sinks == []
    assert warnings == ["hubspot sink requires a HubSpot access token; skipping"]
