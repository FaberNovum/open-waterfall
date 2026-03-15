from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FundingInfo(BaseModel):
    """Funding round information."""

    total_raised: Optional[float] = None
    last_round_type: Optional[str] = None
    last_round_amount: Optional[float] = None
    last_round_date: Optional[datetime] = None
    investors: list[str] = Field(default_factory=list)


class HiringSignals(BaseModel):
    """Hiring activity signals."""

    open_positions: int = 0
    departments_hiring: list[str] = Field(default_factory=list)
    growth_rate: Optional[float] = None


class Company(BaseModel):
    """Portable company model for provider and sink layers."""

    domain: str
    name: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    employee_count: Optional[int] = None
    employee_range: Optional[str] = None
    revenue: Optional[float] = None
    revenue_range: Optional[str] = None
    founded_year: Optional[int] = None
    headquarters_city: Optional[str] = None
    headquarters_state: Optional[str] = None
    headquarters_country: Optional[str] = None
    address: Optional[str] = None
    tech_stack: list[str] = Field(default_factory=list)
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    funding: Optional[FundingInfo] = None
    hiring: Optional[HiringSignals] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    website_context: Optional[str] = None
    linkedin_context: Optional[str] = None
    is_b2b: Optional[bool] = None
    is_public: Optional[bool] = None
    stock_symbol: Optional[str] = None
    enriched_at: Optional[datetime] = None
    enrichment_sources: list[str] = Field(default_factory=list)


class CompanyEnrichmentResult(BaseModel):
    """Result from a company enrichment attempt."""

    success: bool
    company: Optional[Company] = None
    source: str
    error: Optional[str] = None
    fields_enriched: list[str] = Field(default_factory=list)
    raw_response: Optional[dict] = None

