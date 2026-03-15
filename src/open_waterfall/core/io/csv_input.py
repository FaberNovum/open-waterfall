from __future__ import annotations

import pandas as pd


def parse_input_csv(file_path: str) -> pd.DataFrame:
    """Parse a CSV and normalize common input columns."""
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")

    required = ["first_name", "last_name"]
    alternatives = {
        "first_name": ["firstname", "first"],
        "last_name": ["lastname", "last", "surname"],
    }

    missing = [col for col in required if col not in df.columns]
    for col in missing:
        for alt in alternatives.get(col, []):
            if alt in df.columns:
                df[col] = df[alt]
                break

    if "domain" not in df.columns:
        for alt in ["company_domain", "website", "company_website", "organization.primary_domain"]:
            if alt in df.columns:
                df["domain"] = df[alt]
                break
        else:
            df["domain"] = ""

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df

