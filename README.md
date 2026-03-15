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

## New Here

If you are new to the repo, use this order:

1. Run the no-credentials demo.
2. Skim the command guide and system map below.
3. Move to the example that matches your workflow.

The built-in demo is the first command to run:

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
enriched 1 rows using 1 company providers and 1 contact providers -> output/enriched.csv
Running local outbound walkthrough...
generated outbound assets for 1 rows using strategy=cold_email_sequence -> output/outbound.csv
```

## System Map

- `src/open_waterfall/core/`: shared models, config loading, CSV IO, and pipeline primitives
- `src/open_waterfall/providers/`: enrichment providers such as Apollo, Clearbit, Hunter, and the local `demo` provider
- `src/open_waterfall/sourcing/`: lead sources that fetch rows before a CSV exists
- `src/open_waterfall/research/`: optional context modules layered onto enriched leads
- `src/open_waterfall/messaging/`: outbound generators for email and LinkedIn assets
- `src/open_waterfall/sinks/`: CSV and CRM delivery
- `src/open_waterfall/profiles/`: reusable config layers you can compose in your own YAML
- `examples/`: runnable workflows that show the intended setup path

## Command Guide

| Command | You provide | It does | Use it when |
| --- | --- | --- | --- |
| `demo` | nothing beyond the repo checkout | runs the built-in local walkthrough | you want the fastest sanity check |
| `search` | a config with `source.*` enabled | sources leads from a provider and runs the local pipeline | you want the system to fetch leads for you |
| `enrich` | an input CSV | enriches and scores existing rows | you already have a lead list |
| `score` | an input CSV | applies persona classification and scoring | your CSV already has enough company data |
| `message` | an input CSV | generates research and outbound assets | you want email/LinkedIn copy for existing rows |
| `sync` | an input CSV | writes rows to configured sinks | you want HubSpot or other sink delivery |

## Profiles

Shipped profiles are real config layers, not just labels. Use one base profile with `profile:` or compose multiple with `profiles:`.

```yaml
profiles:
  - generic_b2b
  - outbound_csv

providers:
  company_waterfall:
    - demo
  contact_waterfall:
    - demo
```

Profiles are loaded first, then your local config overrides them.

## Credentials

Provider-backed examples expect environment variables. The config loader automatically reads the nearest project `.env`, so the usual path is:

```bash
cp .env.example .env
```

Fill in only the keys you need. Shell-exported variables still win over values in `.env`.

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

- `output/enriched.csv` with contact, company, and scoring fields populated
- `output/outbound.csv` with outbound copy columns populated

## Local Examples

- CSV-first enrich walkthrough: [examples/enrich_to_csv/README.md](examples/enrich_to_csv/README.md)
- CSV-first outbound walkthrough: [examples/outbound_to_csv/README.md](examples/outbound_to_csv/README.md)
- Apollo-first sourced leads walkthrough: [examples/search_apollo/README.md](examples/search_apollo/README.md)
- Optional HubSpot walkthrough: [examples/outbound_hubspot/README.md](examples/outbound_hubspot/README.md)

## Read Next

- [docs/architecture.md](docs/architecture.md)
- [docs/config.md](docs/config.md)
- [docs/profiles.md](docs/profiles.md)

## Design Rules

- `core` stays usable without HubSpot
- messaging is optional even though it ships in v1
- shipped profiles stay generic and free of private defaults
