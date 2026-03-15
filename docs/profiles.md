# Profiles

## Shipped Profiles

- `generic_b2b.yaml`: neutral enrichment and scoring defaults
- `outbound_csv.yaml`: file-first outbound flow
- `outbound_hubspot.yaml`: outbound flow with HubSpot enabled

## Rules

- No personal sender defaults
- No company-specific value props
- No private CRM IDs

## Intended Usage

- Start with `generic_b2b.yaml` for enrichment and scoring.
- Use `outbound_csv.yaml` when you want messaging assets written back to CSV.
- Use `outbound_hubspot.yaml` only when HubSpot sync is explicitly part of the workflow.
