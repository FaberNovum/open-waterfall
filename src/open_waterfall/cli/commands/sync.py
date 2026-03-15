from __future__ import annotations

import click

from open_waterfall.core.config.loader import load_config
from open_waterfall.core.io import dataframe_to_lead_pairs, parse_input_csv
from open_waterfall.sinks import build_sinks


@click.command("sync")
@click.argument("input_csv", type=click.Path(exists=True))
@click.option("--config", "config_path", required=True, type=click.Path(exists=True))
def sync_command(input_csv: str, config_path: str) -> None:
    """Write lead rows to configured sinks."""
    config = load_config(config_path)
    df = parse_input_csv(input_csv)
    lead_pairs = dataframe_to_lead_pairs(df)
    sinks, warnings = build_sinks(config)

    for warning in warnings:
        click.echo(f"warning: {warning}")

    if not sinks:
        raise click.ClickException("No usable sinks configured")

    summaries = [sink.write(lead_pairs, {}) for sink in sinks]
    click.echo(f"sync completed for {len(lead_pairs)} rows: {summaries}")

