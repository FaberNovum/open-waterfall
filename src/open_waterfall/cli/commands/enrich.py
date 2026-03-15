from __future__ import annotations

from pathlib import Path

import click

from open_waterfall.core.config.loader import load_config
from open_waterfall.core.io.csv_output import export_contacts_to_csv
from open_waterfall.core.io.csv_input import parse_input_csv
from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact
from open_waterfall.core.pipeline.waterfall import WaterfallProcessor
from open_waterfall.providers import build_enrichers
from open_waterfall.scoring.lead_scorer import LeadScorer
from open_waterfall.scoring.persona_classifier import PersonaClassifier


@click.command("enrich")
@click.argument("input_csv", type=click.Path(exists=True))
@click.option("--config", "config_path", required=True, type=click.Path(exists=True))
def enrich_command(input_csv: str, config_path: str) -> None:
    """Run the enrichment waterfall and export a CSV."""
    config = load_config(config_path)
    df = parse_input_csv(input_csv)
    company_enrichers, contact_enrichers = build_enrichers(config)
    scorer = LeadScorer(config.scoring.model_dump())
    classifier = PersonaClassifier(config.personas.rules if config.personas.enabled else {})
    processor = WaterfallProcessor(
        company_enrichers=company_enrichers,
        contact_enrichers=contact_enrichers,
        merge_results=config.pipeline.merge_results,
    )

    contacts: list[Contact] = []
    companies: dict[str, Company] = {}

    for row in df.fillna("").to_dict(orient="records"):
        first_name = str(row.get("first_name", "")).strip()
        last_name = str(row.get("last_name", "")).strip()
        domain = str(row.get("domain", "")).strip()
        company_name = str(row.get("company_name", "")).strip() or None

        company = None
        if domain and not config.pipeline.skip_company and company_enrichers:
            company, _company_results = processor.enrich_company(domain)
            if company:
                companies[domain] = company

        enriched_contact = None
        if domain and not config.pipeline.skip_contact and contact_enrichers:
            enriched_contact, _contact_results = processor.enrich_contact(
                first_name=first_name,
                last_name=last_name,
                domain=domain,
                company_name=company_name,
            )

        contact = enriched_contact or Contact(
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}".strip() or None,
            company_domain=domain or None,
            company_name=company_name,
        )
        if config.personas.enabled:
            classifier.assign(contact)
        if config.scoring.enabled:
            scorer.score_lead(contact, company)
        contacts.append(contact)

    output_path = config.sinks.csv.get("output_path", "./output/enriched.csv")
    export_contacts_to_csv(contacts, companies, output_path)

    click.echo(
        f"enriched {len(contacts)} rows using {len(company_enrichers)} company providers and "
        f"{len(contact_enrichers)} contact providers -> {Path(output_path)}"
    )
