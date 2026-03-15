# Contributing

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Tests

```bash
pytest
```

`tests/sinks/test_hubspot.py` is skipped unless the optional HubSpot dependency is installed.

Run the full optional suite with:

```bash
pip install -e ".[dev,hubspot]"
pytest
```

## Lint

```bash
ruff check .
```

## Working Rules

- Keep `core` free of CRM and outbound-specific assumptions.
- Treat messaging as optional, even though it ships in v1.
- Keep shipped profiles generic and free of private operator defaults.
