from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EmailVerificationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    CATCH_ALL = "catch_all"
    UNKNOWN = "unknown"
    SPAMTRAP = "spamtrap"
    ABUSE = "abuse"
    DO_NOT_MAIL = "do_not_mail"
    UNVERIFIED = "unverified"


class Segment(str, Enum):
    HIGH_TOUCH = "high_touch"
    STANDARD = "standard"
    NURTURE = "nurture"


class Contact(BaseModel):
    """Portable contact model for enrichment, scoring, and messaging."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    email_verification_status: EmailVerificationStatus = EmailVerificationStatus.UNVERIFIED
    phone: Optional[str] = None
    mobile: Optional[str] = None
    title: Optional[str] = None
    normalized_title: Optional[str] = None
    seniority: Optional[str] = None
    department: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    icp_score: float = 0.0
    intent_score: float = 0.0
    total_score: float = 0.0
    segment: Segment = Segment.NURTURE
    persona: Optional[str] = None
    linkedin_context: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_icebreaker: Optional[str] = None
    ai_email_variants: list[str] = Field(default_factory=list)
    ai_linkedin_message: Optional[str] = None
    trigger_events: list[str] = Field(default_factory=list)
    recent_linkedin_posts: list[str] = Field(default_factory=list)
    enriched_at: Optional[datetime] = None
    enrichment_sources: list[str] = Field(default_factory=list)
    external_ids: dict[str, str] = Field(default_factory=dict)


class ContactEnrichmentResult(BaseModel):
    """Result from a contact enrichment attempt."""

    success: bool
    contact: Optional[Contact] = None
    source: str
    error: Optional[str] = None
    fields_enriched: list[str] = Field(default_factory=list)
    raw_response: Optional[dict] = None

