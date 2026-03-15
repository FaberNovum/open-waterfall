from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


def _default_hubspot_contact_properties() -> list[str]:
    properties = [
        "enrichment_score",
        "enrichment_segment",
        "enrichment_source",
        "ai_icebreaker",
        "persona_segment",
        "verified_email",
        "email_sequence_ready",
    ]
    for step in range(1, 6):
        properties.extend([f"email_step_{step}_subject", f"email_step_{step}_body"])
    return properties


def _default_hubspot_company_properties() -> list[str]:
    return [
        "enrichment_source",
        "tech_stack",
        "funding_stage",
        "employee_count_range",
        "website_context",
    ]


class ProvidersConfig(BaseModel):
    company_waterfall: list[str] = Field(default_factory=list)
    contact_waterfall: list[str] = Field(default_factory=list)
    api_keys: dict = Field(default_factory=dict)
    settings: dict = Field(default_factory=dict)


class PipelineConfig(BaseModel):
    merge_results: bool = True
    skip_company: bool = False
    skip_contact: bool = False
    skip_research: bool = False
    skip_messaging: bool = False
    skip_sinks: bool = False


class ScoringConfig(BaseModel):
    enabled: bool = True
    weights: dict = Field(default_factory=dict)
    thresholds: dict = Field(default_factory=lambda: {"high_touch": 80, "standard": 50})
    profile: str = "generic_b2b"


class PersonasConfig(BaseModel):
    enabled: bool = True
    rules: dict = Field(default_factory=dict)


class AIConfig(BaseModel):
    model: str = "gpt-4.1-mini"
    temperature: float = 0.4


class ResearchConfig(BaseModel):
    enabled_modules: list[str] = Field(default_factory=list)
    ai: AIConfig = Field(default_factory=AIConfig)


class SenderConfig(BaseModel):
    name: str = "Example Sender"
    company: str = "Example Company"


class MessagingConfig(BaseModel):
    enabled: bool = False
    strategy: str = "cold_email_sequence"
    ai: AIConfig = Field(default_factory=lambda: AIConfig(model="gpt-4.1", temperature=0.7))
    sender: SenderConfig = Field(default_factory=SenderConfig)
    value_prop: str = "Example value proposition"


class HubSpotWorkflowConfig(BaseModel):
    auto_enroll: bool = False
    min_score: Optional[float] = None
    require_verified_email: bool = False
    default_workflow_id: Optional[str] = None
    persona_workflows: dict[str, str] = Field(default_factory=dict)


class HubSpotCustomPropertiesConfig(BaseModel):
    contact: list[str] = Field(default_factory=_default_hubspot_contact_properties)
    company: list[str] = Field(default_factory=_default_hubspot_company_properties)


class HubSpotSinkConfig(BaseModel):
    enabled: bool = False
    access_token: Optional[str] = None
    create_contacts: bool = True
    create_companies: bool = True
    default_owner_id: Optional[str] = None
    custom_properties: HubSpotCustomPropertiesConfig = Field(default_factory=HubSpotCustomPropertiesConfig)
    workflow: HubSpotWorkflowConfig = Field(default_factory=HubSpotWorkflowConfig)


class SinksConfig(BaseModel):
    enabled: list[str] = Field(default_factory=lambda: ["csv"])
    csv: dict = Field(default_factory=lambda: {"output_path": "./output/enriched.csv"})
    hubspot: HubSpotSinkConfig = Field(default_factory=HubSpotSinkConfig)


class RuntimeConfig(BaseModel):
    rate_limits: dict = Field(default_factory=dict)
    checkpointing: bool = True


class OpenWaterfallConfig(BaseModel):
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    personas: PersonasConfig = Field(default_factory=PersonasConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    messaging: MessagingConfig = Field(default_factory=MessagingConfig)
    sinks: SinksConfig = Field(default_factory=SinksConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
