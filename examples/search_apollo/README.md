# Search Apollo

This is the provider-led lead sourcing example. It uses Apollo to fetch leads first, then runs the local pipeline and writes a CSV.

## Prerequisites

- `APOLLO_API_KEY` exported in your shell or placed in `.env`

The config loader automatically reads `.env`, so `cp .env.example .env` is the normal starting point.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
open-waterfall search --config examples/search_apollo/config.yaml
```

The result is written to `./output/sourced.csv`.

If `messaging.enabled` stays on in the example config, the output CSV also includes outbound copy columns.
