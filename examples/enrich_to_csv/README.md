# Enrich to CSV

This is the default local-first example. It does not require HubSpot or any private context.

Because the example config disables provider waterfalls, it is deterministic and does not require API keys.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
open-waterfall enrich examples/enrich_to_csv/leads.csv --config examples/enrich_to_csv/config.yaml
```

Expected CLI output:

```text
enriched 1 rows using 0 company providers and 0 contact providers -> output/enriched.csv
```

The result is written to `./output/enriched.csv` by the CSV sink.

Quick verification:

```bash
sed -n '1,5p' output/enriched.csv
```

You should see a single `Jane Doe` row with scoring columns present.
