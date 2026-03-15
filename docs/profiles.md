# Profiles

Profiles are reusable YAML layers. Load one with `profile:` or compose several with `profiles:`.

```yaml
profiles:
  - generic_b2b
  - outbound_csv
```

Profiles are merged in order, then the local config file overrides the merged result.

## Shipped Profiles

- `generic_b2b.yaml`: neutral enrichment and scoring defaults
- `outbound_csv.yaml`: file-first outbound flow
- `outbound_hubspot.yaml`: outbound flow with HubSpot enabled

## Rules

- No personal sender defaults
- No company-specific value props
- No private CRM IDs

## Intended Usage

- Start with `generic_b2b` for enrichment and scoring defaults.
- Layer `outbound_csv` on top when you want messaging assets written back to CSV.
- Layer `outbound_hubspot` on top only when HubSpot sync is explicitly part of the workflow.

Typical combinations:

- `profile: generic_b2b`
- `profiles: [generic_b2b, outbound_csv]`
- `profiles: [generic_b2b, outbound_hubspot]`
