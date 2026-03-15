# Outbound to CSV

This is the recommended full walkthrough for a new user. It stays file-first, requires no API keys, and proves outbound asset generation is functioning.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
open-waterfall message examples/outbound_to_csv/leads.csv --config examples/outbound_to_csv/config.yaml
```

Expected CLI output:

```text
generated outbound assets for 1 rows using strategy=cold_email_sequence -> output/outbound.csv
```

Quick verification:

```bash
sed -n '1,20p' output/outbound.csv
```

You should see one `Jane Doe` row with `ai_email_variants` and `ai_linkedin_message` populated.
