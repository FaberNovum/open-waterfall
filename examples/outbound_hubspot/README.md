# Outbound HubSpot

This example is optional. The default project story is still file-first.

## Prerequisites

- HubSpot private app token exported as `HUBSPOT_ACCESS_TOKEN`
- HubSpot dependency installed with `pip install -e ".[dev,hubspot]"`

## Run

```bash
cd open-waterfall
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,hubspot]"
open-waterfall sync examples/outbound_hubspot/leads.csv --config examples/outbound_hubspot/config.yaml
```

This writes contact/company data through the HubSpot sink and can optionally enroll workflows when enabled in config.
