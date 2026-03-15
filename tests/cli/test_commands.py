from pathlib import Path

from click.testing import CliRunner

from open_waterfall.cli.app import main
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
