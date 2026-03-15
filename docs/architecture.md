# Architecture

## Layers

- `core`: models, provider interfaces, pipeline, config, IO, ops
- `sourcing`: provider-led lead search before CSV exists
- `scoring`: score and persona classification engines
- `research`: optional AI context generation
- `messaging`: optional outbound generation
- `sinks`: file and CRM delivery
- `providers`: concrete provider implementations

## Rule

`core` must remain reusable without HubSpot, outbound messaging, or a specific market profile.

## Public Extension Points

- Providers implement the base enrichment interfaces and register through the provider bootstrap/registry path.
- Research modules are independently toggleable and attach optional context to lead objects.
- Messaging strategies generate outbound assets without requiring any CRM sink.
- Sinks consume hydrated `Contact` and `Company` objects and own delivery only.

## CLI Flow

Each command follows the same high-level pattern:

1. Load config.
2. Merge any referenced shipped profiles.
3. Load `.env` placeholders and validate config.
4. Read CSV input or source lead objects from a configured provider.
5. Run only the enabled stages for that command.
6. Write outputs to CSV or configured sinks.

## Command Paths

- `demo`: runs the local enrich walkthrough, then the local outbound walkthrough
- `enrich`: CSV in, provider waterfall + scoring/personas, CSV out
- `score`: CSV in, scoring/personas only, CSV out
- `message`: CSV in, optional research + outbound generation, CSV out
- `search`: provider source in, optional enrichment/research/messaging, CSV out
- `sync`: CSV in, configured sinks out

## Onboarding Path

For a new user, the intended sequence is:

1. `open-waterfall demo`
2. `examples/enrich_to_csv`
3. `examples/outbound_to_csv`
4. `examples/search_apollo` once credentials are present
5. `examples/outbound_hubspot` only when CRM sync is actually needed
