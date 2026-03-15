from __future__ import annotations

from typing import Any

from open_waterfall.core.config.schema import HubSpotWorkflowConfig
from open_waterfall.core.models.contact import Contact, EmailVerificationStatus


class HubSpotWorkflowClient:
    def __init__(self, client: Any, config: HubSpotWorkflowConfig | dict | None = None) -> None:
        if isinstance(config, HubSpotWorkflowConfig):
            self.config = config.model_dump()
        else:
            self.config = dict(config or {})
        self.client = client

    def should_enroll(self, contact: Contact) -> bool:
        if not self.config.get("auto_enroll", False):
            return False
        if not contact.email:
            return False

        min_score = self.config.get("min_score")
        if min_score is not None and contact.total_score < float(min_score):
            return False

        if self.config.get("require_verified_email", False):
            return contact.email_verification_status == EmailVerificationStatus.VALID

        return True

    def resolve_workflow_id(self, contact: Contact) -> str:
        persona_workflows = self.config.get("persona_workflows", {})
        if contact.persona and persona_workflows.get(contact.persona):
            return str(persona_workflows[contact.persona])
        return str(self.config.get("default_workflow_id") or "")

    def enroll(self, contact: Contact) -> bool:
        workflow_id = self.resolve_workflow_id(contact)
        if not contact.email or not workflow_id:
            return False

        try:
            response = self.client.api_request(
                {
                    "path": f"/automation/v2/workflows/{workflow_id}/enrollments/contacts/{contact.email}",
                    "method": "POST",
                }
            )
        except Exception:
            return False

        return response.status_code in (200, 201, 204)
