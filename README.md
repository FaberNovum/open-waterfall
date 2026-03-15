# Open Waterfall

`open-waterfall` is a Python toolkit for company/contact enrichment, configurable scoring, AI research, outbound messaging, and optional CRM sync.

## Goals

- Provider-agnostic enrichment waterfall
- Configurable scoring and personas
- Optional AI research and outbound messaging
- File-first default workflow
- Optional CRM sinks such as HubSpot

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
open-waterfall --help
```

Install HubSpot support only if you need CRM sync:

```bash
pip install -e ".[dev,hubspot]"
```

## 5-Minute Verification

This is the default first-run path. It requires no API keys and proves the CLI, config loader, CSV IO, scoring, and CSV-first messaging flow are working.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
open-waterfall enrich examples/enrich_to_csv/leads.csv --config examples/enrich_to_csv/config.yaml
open-waterfall message examples/outbound_to_csv/leads.csv --config examples/outbound_to_csv/config.yaml
```

Expected command output:

```text
enriched 1 rows using 0 company providers and 0 contact providers -> output/enriched.csv
generated outbound assets for 1 rows using strategy=cold_email_sequence -> output/outbound.csv
```

Expected artifacts:

- `output/enriched.csv` with one lead row
- `output/outbound.csv` with fallback email sequence and LinkedIn message columns populated

## Commands

```bash
open-waterfall enrich leads.csv --config src/open_waterfall/profiles/generic_b2b.yaml
open-waterfall score leads.csv --config src/open_waterfall/profiles/generic_b2b.yaml
open-waterfall message leads.csv --config src/open_waterfall/profiles/outbound_csv.yaml
open-waterfall sync leads.csv --config src/open_waterfall/profiles/outbound_hubspot.yaml
```

## Profiles

- `generic_b2b.yaml`: neutral enrichment and scoring defaults
- `outbound_csv.yaml`: file-first outbound flow
- `outbound_hubspot.yaml`: outbound plus optional HubSpot sync

## Local Examples

- CSV-first enrich walkthrough: [examples/enrich_to_csv/README.md](examples/enrich_to_csv/README.md)
- CSV-first outbound walkthrough: [examples/outbound_to_csv/README.md](examples/outbound_to_csv/README.md)
- Optional HubSpot walkthrough: [examples/outbound_hubspot/README.md](examples/outbound_hubspot/README.md)

## Design Rules

- `core` stays usable without HubSpot
- messaging is optional even though it ships in v1
- shipped profiles stay generic and free of private defaults
