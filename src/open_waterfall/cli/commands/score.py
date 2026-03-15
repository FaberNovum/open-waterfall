from __future__ import annotations

from pathlib import Path

import click

from open_waterfall.core.config.loader import load_config
from open_waterfall.core.io import dataframe_to_lead_pairs, export_contacts_to_csv, parse_input_csv
from open_waterfall.scoring.lead_scorer import LeadScorer
from open_waterfall.scoring.persona_classifier import PersonaClassifier


@click.command("score")
@click.argument("input_csv", type=click.Path(exists=True))
@click.option("--config", "config_path", required=True, type=click.Path(exists=True))
def score_command(input_csv: str, config_path: str) -> None:
    """Apply persona classification and lead scoring to CSV input."""
    config = load_config(config_path)
    df = parse_input_csv(input_csv)
    lead_pairs = dataframe_to_lead_pairs(df)
    scorer = LeadScorer(config.scoring.model_dump())
    classifier = PersonaClassifier(config.personas.rules if config.personas.enabled else {})

    contacts = []
    companies = {}
    for contact, company in lead_pairs:
        if config.personas.enabled:
            classifier.assign(contact)
        if config.scoring.enabled:
            scorer.score_lead(contact, company)
        contacts.append(contact)
        if company and company.domain:
            companies[company.domain] = company

    output_path = config.sinks.csv.get("output_path", "./output/scored.csv")
    export_contacts_to_csv(contacts, companies, output_path)
    click.echo(f"scored {len(contacts)} rows with profile={config.scoring.profile} -> {Path(output_path)}")
