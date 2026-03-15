from __future__ import annotations

from typing import Optional

import pandas as pd

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact, EmailVerificationStatus, Segment


EMAIL_VARIANT_SEPARATOR = "\n\n===\n\n"


def _clean_str(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _clean_int(value: object) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _clean_float(value: object) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_list(value: object, separator: str = ",") -> list[str]:
    text = _clean_str(value)
    if not text:
        return []
    return [item.strip() for item in text.split(separator) if item.strip()]


def _clean_email_variants(value: object) -> list[str]:
    text = _clean_str(value)
    if not text:
        return []
    return [item.strip() for item in text.split(EMAIL_VARIANT_SEPARATOR) if item.strip()]


def row_to_lead_pair(row: dict) -> tuple[Contact, Optional[Company]]:
    domain = _clean_str(
        row.get("domain")
        or row.get("company_domain")
        or row.get("website")
        or row.get("company_website")
    )
    company_name = _clean_str(row.get("company_name"))
    first_name = _clean_str(row.get("first_name"))
    last_name = _clean_str(row.get("last_name"))
    full_name = _clean_str(row.get("full_name")) or " ".join(filter(None, [first_name, last_name])) or None

    contact = Contact(
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        company_domain=domain,
        company_name=company_name,
        email=_clean_str(row.get("email")),
        phone=_clean_str(row.get("phone")),
        mobile=_clean_str(row.get("mobile")),
        title=_clean_str(row.get("title")),
        seniority=_clean_str(row.get("seniority")),
        department=_clean_str(row.get("department")),
        linkedin_url=_clean_str(row.get("linkedin_url")),
        twitter_url=_clean_str(row.get("twitter_url")),
        city=_clean_str(row.get("city")),
        state=_clean_str(row.get("state")),
        country=_clean_str(row.get("country")),
        ai_summary=_clean_str(row.get("ai_summary")),
        ai_icebreaker=_clean_str(row.get("ai_icebreaker")),
        ai_email_variants=_clean_email_variants(row.get("ai_email_variants")),
        ai_linkedin_message=_clean_str(row.get("ai_linkedin_message")),
        persona=_clean_str(row.get("persona")),
        icp_score=_clean_float(row.get("icp_score")) or 0.0,
        intent_score=_clean_float(row.get("intent_score")) or 0.0,
        total_score=_clean_float(row.get("total_score")) or 0.0,
        enrichment_sources=_clean_list(row.get("enrichment_sources")),
    )

    verification_status = _clean_str(row.get("email_verification_status") or row.get("verified_email"))
    if verification_status in {item.value for item in EmailVerificationStatus}:
        contact.email_verification_status = EmailVerificationStatus(verification_status)

    segment = _clean_str(row.get("segment"))
    if segment in {item.value for item in Segment}:
        contact.segment = Segment(segment)

    company_industry = _clean_str(row.get("company_industry") or row.get("industry"))
    company_employee_count = _clean_int(row.get("company_employee_count") or row.get("employee_count"))
    company_revenue = _clean_float(row.get("company_revenue") or row.get("revenue"))

    company = None
    if domain or company_name or company_industry or company_employee_count or company_revenue:
        company = Company(
            domain=domain or "",
            name=company_name,
            industry=company_industry,
            employee_count=company_employee_count,
            revenue=company_revenue,
            description=_clean_str(row.get("company_description") or row.get("description")),
            website_context=_clean_str(row.get("website_context")),
            linkedin_url=_clean_str(row.get("company_linkedin_url")),
            employee_range=_clean_str(row.get("employee_range") or row.get("company_employee_range")),
            enrichment_sources=_clean_list(row.get("company_enrichment_sources")),
        )

    return contact, company


def dataframe_to_lead_pairs(df: pd.DataFrame) -> list[tuple[Contact, Optional[Company]]]:
    return [row_to_lead_pair(record) for record in df.fillna("").to_dict(orient="records")]
