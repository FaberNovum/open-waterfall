# Config

Profiles live under `src/open_waterfall/profiles/`.

Top-level sections:

- `providers`
- `pipeline`
- `scoring`
- `personas`
- `research`
- `messaging`
- `sinks`
- `runtime`

## Providers

- `company_waterfall`: ordered provider names for company enrichment
- `contact_waterfall`: ordered provider names for contact enrichment
- `api_keys`: provider credentials, usually sourced from environment variables
- `settings`: provider-specific overrides

## Pipeline

- `merge_results`: merge partial provider results when multiple enrichers succeed
- `skip_company`, `skip_contact`, `skip_research`, `skip_messaging`, `skip_sinks`: disable stages explicitly

## Scoring And Personas

- `scoring.profile`: shipped neutral profile name
- `scoring.weights` and `scoring.thresholds`: scoring behavior
- `personas.rules`: persona keyword/rule configuration

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
