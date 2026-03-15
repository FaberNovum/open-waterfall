from __future__ import annotations

from pathlib import Path

import click

from open_waterfall.cli.commands.enrich import enrich_command
from open_waterfall.cli.commands.message import message_command


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


@click.command("demo")
@click.pass_context
def demo_command(ctx: click.Context) -> None:
    """Run the built-in no-credentials walkthrough."""
    root = _repo_root()
    enrich_input = root / "examples" / "enrich_to_csv" / "leads.csv"
    enrich_config = root / "examples" / "enrich_to_csv" / "config.yaml"
    outbound_input = root / "examples" / "outbound_to_csv" / "leads.csv"
    outbound_config = root / "examples" / "outbound_to_csv" / "config.yaml"

    required_paths = [enrich_input, enrich_config, outbound_input, outbound_config]
    missing_paths = [str(path) for path in required_paths if not path.exists()]
    if missing_paths:
        raise click.ClickException(
            "demo files are missing. Run this command from an editable checkout of the repository."
        )

    click.echo("Running local enrich walkthrough...")
    ctx.invoke(enrich_command, input_csv=str(enrich_input), config_path=str(enrich_config))
    click.echo("Running local outbound walkthrough...")
    ctx.invoke(message_command, input_csv=str(outbound_input), config_path=str(outbound_config))
