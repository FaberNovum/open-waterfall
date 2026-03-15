from __future__ import annotations

from typing import Optional, Tuple

from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact, Segment


class LeadScorer:
    """Generic profile-driven lead scorer."""

    def __init__(self, config: dict, personas: Optional[dict] = None):
        self.config = config or {}
        self.personas = personas or {}

    def score_lead(self, contact: Contact, company: Optional[Company]) -> Contact:
        if company is None:
            contact.icp_score = 0.0
            contact.intent_score = 0.0
            contact.total_score = 0.0
            contact.segment = Segment.NURTURE
            return contact

        weights = self.config.get("weights", {})
        icp = self.config.get("icp", {})
        thresholds = self.config.get("thresholds", self.config.get("segments", {}))

        score = 0.0

        industries = [value.lower() for value in icp.get("industries", [])]
        industry_weight = weights.get("industry_match", 0)
        if company.industry:
            industry = company.industry.lower()
            if industry in industries:
                score += industry_weight
            elif any(term in industry or industry in term for term in industries):
                score += industry_weight / 2

        min_revenue = icp.get("min_revenue")
        max_revenue = icp.get("max_revenue")
        revenue_weight = weights.get("revenue_fit", 0)
        if company.revenue is not None and min_revenue is not None and max_revenue is not None:
            if min_revenue <= company.revenue <= max_revenue:
                score += revenue_weight

        min_employees = icp.get("min_employees")
        max_employees = icp.get("max_employees")
        employee_weight = weights.get("employee_fit", 0)
        if company.employee_count is not None and min_employees is not None and max_employees is not None:
            if min_employees <= company.employee_count <= max_employees:
                score += employee_weight

        required_tech = [value.lower() for value in icp.get("required_tech", [])]
        tech_weight = weights.get("tech_match", 0)
        if required_tech and company.tech_stack:
            matches = len(set(required_tech).intersection({tech.lower() for tech in company.tech_stack}))
            score += tech_weight * (matches / len(required_tech))

        contact.icp_score = round(score, 2)
        contact.intent_score = 0.0
        contact.total_score = min(100.0, round(contact.icp_score + contact.intent_score, 2))
        contact.segment = self._assign_segment(contact.total_score, thresholds)
        return contact

    def score_batch(self, leads: list[Tuple[Contact, Optional[Company]]]) -> list[Contact]:
        return [self.score_lead(contact, company) for contact, company in leads]

    def _assign_segment(self, total_score: float, thresholds: dict) -> Segment:
        high_touch = thresholds.get("high_touch", 80)
        standard = thresholds.get("standard", 50)
        if total_score >= high_touch:
            return Segment.HIGH_TOUCH
        if total_score >= standard:
            return Segment.STANDARD
        return Segment.NURTURE
