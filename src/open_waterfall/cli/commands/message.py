from __future__ import annotations

from pathlib import Path

import click

from open_waterfall.core.config.loader import load_config
from open_waterfall.core.io import dataframe_to_lead_pairs, export_contacts_to_csv, parse_input_csv
from open_waterfall.messaging import build_message_strategies
from open_waterfall.research import build_research_modules
from open_waterfall.scoring.lead_scorer import LeadScorer
from open_waterfall.scoring.persona_classifier import PersonaClassifier


@click.command("message")
@click.argument("input_csv", type=click.Path(exists=True))
@click.option("--config", "config_path", required=True, type=click.Path(exists=True))
def message_command(input_csv: str, config_path: str) -> None:
    """Generate research context and outbound assets for leads."""
    config = load_config(config_path)
    df = parse_input_csv(input_csv)
    lead_pairs = dataframe_to_lead_pairs(df)
    scorer = LeadScorer(config.scoring.model_dump())
    classifier = PersonaClassifier(config.personas.rules if config.personas.enabled else {})
    research_modules = build_research_modules(config) if not config.pipeline.skip_research else []
    email_strategy, linkedin_strategy = build_message_strategies(config)
    context = {
        "sender_name": config.messaging.sender.name,
        "sender_company": config.messaging.sender.company,
        "value_prop": config.messaging.value_prop,
    }

    contacts = []
    companies = {}
    for contact, company in lead_pairs:
        if config.personas.enabled:
            classifier.assign(contact)
        if config.scoring.enabled:
            scorer.score_lead(contact, company)
        for module in research_modules:
            contact = module.run(contact, company, {})
        if config.messaging.enabled:
            contact = email_strategy.generate(contact, company, context)
            contact = linkedin_strategy.generate(contact, company, context)
        contacts.append(contact)
        if company and company.domain:
            companies[company.domain] = company

    output_path = config.sinks.csv.get("output_path", "./output/messages.csv")
    export_contacts_to_csv(contacts, companies, output_path)
    click.echo(
        f"generated outbound assets for {len(contacts)} rows using strategy={config.messaging.strategy} -> {Path(output_path)}"
    )
