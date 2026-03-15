# Config

Profiles live under `src/open_waterfall/profiles/`.

Top-level sections:

- `profile` or `profiles`
- `providers`
- `pipeline`
- `scoring`
- `personas`
- `source`
- `research`
- `messaging`
- `sinks`
- `runtime`

## Profile Loading

- `profile`: load one shipped or local YAML profile before validating the config
- `profiles`: load multiple profiles in order and merge them left to right
- local config values override anything loaded from profiles

Example:

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

## Providers

- `company_waterfall`: ordered provider names for company enrichment
- `contact_waterfall`: ordered provider names for contact enrichment
- `api_keys`: provider credentials, usually sourced from environment variables
- `settings`: provider-specific overrides

## Pipeline

- `merge_results`: merge partial provider results when multiple enrichers succeed
- `skip_company`, `skip_contact`, `skip_research`, `skip_messaging`: disable stages explicitly

## Scoring And Personas

- `scoring.profile`: descriptive label for the active scoring rules
- `scoring.weights` and `scoring.thresholds`: scoring behavior
- `personas.rules`: persona keyword/rule configuration

## Source

- `enabled`: turn provider-led sourcing on or off
- `provider`: current first-party source name, currently `apollo`
- `max_results`: max leads to keep after sourcing
- `page_size`: provider page size
- `min_score`: optional post-score cutoff for keeping sourced leads
- `filters.titles`: source-side title filters
- `filters.seniorities`: source-side seniority filters
- `filters.locations`: source-side company/person location filters
- `filters.employee_ranges`: source-side employee count range filters
- `filters.email_status`: source-side email quality filters

## Research

- `enabled_modules`: any subset of `contact_summary`, `trigger_detection`, `website_context`
- `ai`: model and temperature for AI-backed modules

## Messaging

- `enabled`: turn outbound generation on or off
- `strategy`: current first-party strategy name
- `sender`: sender metadata injected into prompts/fallback copy
- `value_prop`: neutral offer/value statement

## Sinks

- `enabled`: ordered sink list such as `csv` or `hubspot`
- `csv.output_path`: file output destination
- `hubspot.enabled`: opt-in switch for HubSpot
- `hubspot.access_token`: HubSpot private app token
- `hubspot.create_contacts` and `hubspot.create_companies`: sync toggles
- `hubspot.workflow`: optional post-sync enrollment settings

## Environment Variables

Common variables:

- `OPENAI_API_KEY`
- `APOLLO_API_KEY`
- `CLEARBIT_API_KEY`
- `ZOOMINFO_API_KEY`
- `HUNTER_API_KEY`
- `PROSPEO_API_KEY`
- `DROPCONTACT_API_KEY`
- `ZEROBOUNCE_API_KEY`
- `PHANTOMBUSTER_API_KEY`
- `HUBSPOT_ACCESS_TOKEN`

Config files support basic `${ENV_VAR}` substitution at load time.

The loader automatically reads the nearest project `.env` file before substitution. Shell-exported variables keep priority over `.env` values.

## Runtime

`runtime.*` exists for extension work and lower-level integrations. The stock CLI commands do not currently use those settings directly.
