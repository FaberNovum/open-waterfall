from __future__ import annotations

from typing import Optional

from open_waterfall.core.models.company import CompanyEnrichmentResult
from open_waterfall.core.models.contact import Contact, ContactEnrichmentResult, EmailVerificationStatus
from open_waterfall.core.providers.base import BaseEnricher


class ZeroBounceEnricher(BaseEnricher):
    name = "zerobounce"
    base_url = "https://api.zerobounce.net/v2"

    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        return CompanyEnrichmentResult(
            success=False,
            source=self.name,
            error="ZeroBounce does not support company enrichment",
        )

    def enrich_contact(
        self,
        first_name: str,
        last_name: str,
        domain: str,
        company_name: Optional[str] = None,
    ) -> ContactEnrichmentResult:
        return ContactEnrichmentResult(
            success=False,
            source=self.name,
            error="ZeroBounce does not support contact finding. Use verify_email instead.",
        )

    def verify_email(self, email: str, ip_address: Optional[str] = None) -> dict:
        try:
            params = {"api_key": self.api_key, "email": email}
            if ip_address:
                params["ip_address"] = ip_address
            response = self._make_request("GET", "/validate", params=params)
            return {
                "email": email,
                "status": response.get("status"),
                "sub_status": response.get("sub_status"),
                "account": response.get("account"),
                "domain": response.get("domain"),
                "did_you_mean": response.get("did_you_mean"),
                "domain_age_days": response.get("domain_age_days"),
                "free_email": response.get("free_email"),
                "mx_found": response.get("mx_found"),
                "mx_record": response.get("mx_record"),
                "smtp_provider": response.get("smtp_provider"),
                "first_name": response.get("firstname"),
                "last_name": response.get("lastname"),
                "gender": response.get("gender"),
                "city": response.get("city"),
                "region": response.get("region"),
                "country": response.get("country"),
                "processed_at": response.get("processed_at"),
            }
        except Exception as exc:
            return {"email": email, "status": "error", "error": str(exc)}

    def verify_batch(self, emails: list[str]) -> list[dict]:
        return [self.verify_email(email) for email in emails]

    def get_credits(self) -> dict:
        try:
            response = self._make_request("GET", "/getcredits", params={"api_key": self.api_key})
            return {"credits": response.get("Credits", 0)}
        except Exception as exc:
            return {"credits": -1, "error": str(exc)}

    @staticmethod
    def map_status_to_enum(status: str, sub_status: Optional[str] = None) -> EmailVerificationStatus:
        status_lower = status.lower() if status else ""
        if status_lower == "valid":
            return EmailVerificationStatus.VALID
        if status_lower == "invalid":
            return EmailVerificationStatus.INVALID
        if status_lower == "catch-all":
            return EmailVerificationStatus.CATCH_ALL
        if status_lower == "unknown":
            return EmailVerificationStatus.UNKNOWN
        if status_lower == "spamtrap":
            return EmailVerificationStatus.SPAMTRAP
        if status_lower == "abuse":
            return EmailVerificationStatus.ABUSE
        if status_lower == "do_not_mail":
            return EmailVerificationStatus.DO_NOT_MAIL
        return EmailVerificationStatus.UNKNOWN

    def verify_and_update_contact(self, contact: Contact) -> Contact:
        if not contact.email:
            contact.email_verification_status = EmailVerificationStatus.UNVERIFIED
            return contact
        result = self.verify_email(contact.email)
        contact.email_verification_status = self.map_status_to_enum(result.get("status", "unknown"), result.get("sub_status"))
        if result.get("first_name") and not contact.first_name:
            contact.first_name = result["first_name"]
        if result.get("last_name") and not contact.last_name:
            contact.last_name = result["last_name"]
        if result.get("city") and not contact.city:
            contact.city = result["city"]
        if result.get("country") and not contact.country:
            contact.country = result["country"]
        return contact
