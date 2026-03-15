# Outbound to CSV

This is the second half of the recommended walkthrough. It takes the enriched demo output and generates outbound assets from it.

The example uses `profiles: [generic_b2b, outbound_csv]`, so it inherits the shared scoring defaults and layers outbound generation on top.

## Run

```bash
open-waterfall enrich examples/enrich_to_csv/leads.csv --config examples/enrich_to_csv/config.yaml
open-waterfall message output/enriched.csv --config examples/outbound_to_csv/config.yaml
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
