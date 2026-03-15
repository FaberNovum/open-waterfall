from open_waterfall.core.models.company import Company
from open_waterfall.core.models.contact import Contact, Segment
from open_waterfall.scoring.lead_scorer import LeadScorer


def test_perfect_icp_match_scores_high_touch() -> None:
    scorer = LeadScorer(
        {
            "icp": {
                "industries": ["SaaS"],
                "min_revenue": 1_000_000,
                "max_revenue": 100_000_000,
                "min_employees": 50,
                "max_employees": 1_000,
                "required_tech": ["Salesforce", "HubSpot"],
            },
            "weights": {
                "industry_match": 30,
                "revenue_fit": 25,
                "employee_fit": 20,
                "tech_match": 25,
            },
            "thresholds": {"high_touch": 80, "standard": 50},
        }
    )
    company = Company(
        domain="example.com",
        industry="SaaS",
        revenue=5_000_000,
        employee_count=200,
        tech_stack=["Salesforce", "HubSpot"],
    )

    contact = scorer.score_lead(Contact(first_name="Jane"), company)

    assert contact.total_score == 100.0
    assert contact.segment == Segment.HIGH_TOUCH

