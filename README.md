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

## Start Here

If you are new to the repo, run the built-in demo:

```bash
open-waterfall demo
```

This runs the two no-credentials walkthroughs and writes:

- `output/enriched.csv`
- `output/outbound.csv`

## 5-Minute Verification

This is the explicit first-run path behind `open-waterfall demo`. It requires no API keys and proves the CLI, config loader, CSV IO, scoring, and CSV-first messaging flow are working.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
open-waterfall demo
```

Expected output:

```text
Running local enrich walkthrough...
enriched 1 rows using 0 company providers and 0 contact providers -> output/enriched.csv
Running local outbound walkthrough...
generated outbound assets for 1 rows using strategy=cold_email_sequence -> output/outbound.csv
```

## Command Guide

| Command | You provide | It does | Use it when |
| --- | --- | --- | --- |
| `demo` | nothing beyond the repo checkout | runs the built-in local walkthrough | you want the fastest sanity check |
| `search` | a config with `source.*` enabled | sources leads from a provider and runs the local pipeline | you want the system to fetch leads for you |
| `enrich` | an input CSV | enriches and scores existing rows | you already have a lead list |
| `score` | an input CSV | applies persona classification and scoring | your CSV already has enough company data |
| `message` | an input CSV | generates research and outbound assets | you want email/LinkedIn copy for existing rows |
| `sync` | an input CSV | writes rows to configured sinks | you want HubSpot or other sink delivery |

## Provider-Led Search

Apollo-first sourcing is now built in. Configure `source.provider: apollo`, define source filters, and run:

```bash
open-waterfall search --config examples/search_apollo/config.yaml
```

That path still uses your scoring config and can also generate messaging if `messaging.enabled: true`.

## Input CSV

When you are using `enrich`, `score`, `message`, or `sync`, the minimum useful columns are:

- `first_name`
- `last_name`
- `domain`
- `company_name`
- `title`

`first_name` and `last_name` are required. `domain` is strongly recommended because most enrichment logic keys off company domain.

## Expected Artifacts

- `output/enriched.csv` with one lead row
- `output/outbound.csv` with fallback email sequence and LinkedIn message columns populated

## Profiles

- `generic_b2b.yaml`: neutral enrichment and scoring defaults
- `outbound_csv.yaml`: file-first outbound flow
- `outbound_hubspot.yaml`: outbound plus optional HubSpot sync

## Local Examples

- CSV-first enrich walkthrough: [examples/enrich_to_csv/README.md](examples/enrich_to_csv/README.md)
- CSV-first outbound walkthrough: [examples/outbound_to_csv/README.md](examples/outbound_to_csv/README.md)
- Apollo-first sourced leads walkthrough: [examples/search_apollo/README.md](examples/search_apollo/README.md)
- Optional HubSpot walkthrough: [examples/outbound_hubspot/README.md](examples/outbound_hubspot/README.md)

## Design Rules

- `core` stays usable without HubSpot
- messaging is optional even though it ships in v1
- shipped profiles stay generic and free of private defaults
