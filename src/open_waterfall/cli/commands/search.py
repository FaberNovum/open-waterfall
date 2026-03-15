from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from open_waterfall.core.config.loader import load_config
from open_waterfall.core.io.csv_output import export_contacts_to_csv
from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact, EmailVerificationStatus
from open_waterfall.core.pipeline.waterfall import WaterfallProcessor
from open_waterfall.messaging import build_message_strategies
from open_waterfall.providers import build_enrichers
from open_waterfall.research import build_research_modules
from open_waterfall.scoring.lead_scorer import LeadScorer
from open_waterfall.scoring.persona_classifier import PersonaClassifier
from open_waterfall.sourcing import build_lead_source


def _merge_lists(existing: list[str], new_values: list[str]) -> list[str]:
    return list(dict.fromkeys([*existing, *new_values]))


def _merge_company(source_company: Optional[Company], enriched_company: Optional[Company]) -> Optional[Company]:
    if source_company is None:
        return enriched_company
    if enriched_company is None:
        return source_company

    merged_data = source_company.model_dump()
    for field, value in enriched_company.model_dump().items():
        if field in {"enrichment_sources", "enriched_at"}:
            continue
        existing = merged_data.get(field)
        if existing in (None, "", []):
            merged_data[field] = value
        elif isinstance(existing, list) and isinstance(value, list):
            merged_data[field] = _merge_lists(existing, value)

    merged_company = Company(**merged_data)
    merged_company.enriched_at = enriched_company.enriched_at or source_company.enriched_at
    merged_company.enrichment_sources = _merge_lists(
        source_company.enrichment_sources,
        enriched_company.enrichment_sources,
    )
    return merged_company


def _merge_contact(source_contact: Contact, enriched_contact: Optional[Contact]) -> Contact:
    if enriched_contact is None:
        return source_contact

    merged_data = source_contact.model_dump()
    for field, value in enriched_contact.model_dump().items():
        if field in {
            "enrichment_sources",
            "enriched_at",
            "icp_score",
            "intent_score",
            "total_score",
            "segment",
            "external_ids",
            "email_verification_status",
        }:
            continue
        existing = merged_data.get(field)
        if existing in (None, "", []):
            merged_data[field] = value
        elif isinstance(existing, list) and isinstance(value, list):
            merged_data[field] = _merge_lists(existing, value)
        elif isinstance(existing, dict) and isinstance(value, dict):
            merged_data[field] = {**existing, **value}

    merged_contact = Contact(**merged_data)
    merged_contact.enriched_at = enriched_contact.enriched_at or source_contact.enriched_at
    merged_contact.enrichment_sources = _merge_lists(
        source_contact.enrichment_sources,
        enriched_contact.enrichment_sources,
    )
    merged_contact.external_ids = {**source_contact.external_ids, **enriched_contact.external_ids}
    if source_contact.email_verification_status == EmailVerificationStatus.UNVERIFIED:
        merged_contact.email_verification_status = enriched_contact.email_verification_status
    else:
        merged_contact.email_verification_status = source_contact.email_verification_status
    return merged_contact


@click.command("search")
@click.option("--config", "config_path", required=True, type=click.Path(exists=True))
def search_command(config_path: str) -> None:
    """Source leads from a provider and run the local pipeline without an input CSV."""
    config = load_config(config_path)
    source, warnings = build_lead_source(config)

    for warning in warnings:
        click.echo(f"warning: {warning}")

    if source is None:
        raise click.ClickException("No usable lead source configured")

    sourced_pairs = source.search(config.source)

    company_enrichers, contact_enrichers = build_enrichers(config)
    processor = WaterfallProcessor(
        company_enrichers=company_enrichers,
        contact_enrichers=contact_enrichers,
        merge_results=config.pipeline.merge_results,
    )
    scorer = LeadScorer(config.scoring.model_dump())
    classifier = PersonaClassifier(config.personas.rules if config.personas.enabled else {})
    research_modules = build_research_modules(config) if not config.pipeline.skip_research else []
    email_strategy = None
    linkedin_strategy = None
    if config.messaging.enabled and not config.pipeline.skip_messaging:
        email_strategy, linkedin_strategy = build_message_strategies(config)

    contacts: list[Contact] = []
    companies: dict[str, Company] = {}
    skipped_low_score = 0

    for source_contact, source_company in sourced_pairs:
        contact = source_contact.model_copy(deep=True)
        company = source_company.model_copy(deep=True) if source_company else None

        domain = contact.company_domain or (company.domain if company else "")
        company_name = contact.company_name or (company.name if company else None)

        if domain and not config.pipeline.skip_company and company_enrichers:
            enriched_company, _company_results = processor.enrich_company(domain)
            company = _merge_company(company, enriched_company)

        if domain and not config.pipeline.skip_contact and contact_enrichers:
            enriched_contact, _contact_results = processor.enrich_contact(
                first_name=contact.first_name or "",
                last_name=contact.last_name or "",
                domain=domain,
                company_name=company_name,
            )
            contact = _merge_contact(contact, enriched_contact)

        contact.company_domain = contact.company_domain or domain or None
        contact.company_name = contact.company_name or company_name

        if config.personas.enabled:
            classifier.assign(contact)
        if config.scoring.enabled:
            scorer.score_lead(contact, company)
        if config.source.min_score is not None and contact.total_score < config.source.min_score:
            skipped_low_score += 1
            continue

        for module in research_modules:
            contact = module.run(contact, company, {})
        if email_strategy and linkedin_strategy:
            context = {
                "sender_name": config.messaging.sender.name,
                "sender_company": config.messaging.sender.company,
                "value_prop": config.messaging.value_prop,
            }
            contact = email_strategy.generate(contact, company, context)
            contact = linkedin_strategy.generate(contact, company, context)

        contacts.append(contact)
        if company and company.domain:
            companies[company.domain] = company

    output_path = config.sinks.csv.get("output_path", "./output/sourced.csv")
    export_contacts_to_csv(contacts, companies, output_path)
    click.echo(
        f"sourced {len(contacts)} leads from {source.name} "
        f"(filtered_out={skipped_low_score}) -> {Path(output_path)}"
    )
