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
2. Read CSV input or source lead objects from a configured provider.
3. Run only the enabled stages for that command.
4. Write outputs to CSV or configured sinks.
