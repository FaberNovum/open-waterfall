from __future__ import annotations

import json
import time
from typing import Optional

import httpx

from open_waterfall.core.models.company import Company, CompanyEnrichmentResult
from open_waterfall.core.models.contact import Contact, ContactEnrichmentResult
from open_waterfall.core.providers.base import BaseEnricher


PHANTOMBUSTER_API_BASE = "https://api.phantombuster.com/api/v2"


class LinkedInEnricher(BaseEnricher):
    name = "linkedin"

    def __init__(
        self,
        api_key: str,
        profile_phantom_id: str = "",
        company_phantom_id: str = "",
        poll_interval: float = 5.0,
        poll_timeout: float = 120.0,
    ):
        super().__init__(api_key=api_key, timeout=30.0)
        self.profile_phantom_id = profile_phantom_id
        self.company_phantom_id = company_phantom_id
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout
        self._client = httpx.Client(
            timeout=30.0,
            headers={"X-Phantombuster-Key-1": api_key, "Content-Type": "application/json"},
        )

    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        return CompanyEnrichmentResult(
            success=False,
            source="linkedin",
            error="Use enrich_company_linkedin() with a LinkedIn URL",
        )

    def enrich_company_linkedin(self, linkedin_url: str, domain: str = "") -> CompanyEnrichmentResult:
        if not linkedin_url:
            return CompanyEnrichmentResult(success=False, source="linkedin", error="No LinkedIn URL provided")
        if not self.company_phantom_id:
            return CompanyEnrichmentResult(success=False, source="linkedin", error="No company phantom ID configured")
        try:
            container_id = self._launch_phantom(self.company_phantom_id, {"spreadsheetUrl": linkedin_url})
            if not container_id:
                return CompanyEnrichmentResult(success=False, source="linkedin", error="Failed to launch company phantom")
            output = self._poll_results(container_id)
            if not output:
                return CompanyEnrichmentResult(success=False, source="linkedin", error="Company phantom returned no results")
            linkedin_context = self._parse_company_results(output)
            if not linkedin_context:
                return CompanyEnrichmentResult(
                    success=False,
                    source="linkedin",
                    error="Could not extract LinkedIn context from company phantom output",
                )
            company = Company(
                domain=domain,
                linkedin_url=linkedin_url,
                linkedin_context=linkedin_context,
                enrichment_sources=["linkedin"],
            )
            return CompanyEnrichmentResult(
                success=True,
                company=company,
                source="linkedin",
                fields_enriched=["linkedin_context"],
                raw_response=output if isinstance(output, dict) else {"raw": str(output)},
            )
        except Exception as exc:
            return CompanyEnrichmentResult(success=False, source="linkedin", error=str(exc))

    def enrich_contact(
        self,
        first_name: str,
        last_name: str,
        domain: str,
        company_name: Optional[str] = None,
    ) -> ContactEnrichmentResult:
        return ContactEnrichmentResult(
            success=False,
            source="linkedin",
            error="Use enrich_contact_linkedin() with a LinkedIn URL",
        )

    def enrich_contact_linkedin(self, linkedin_url: str) -> ContactEnrichmentResult:
        if not linkedin_url:
            return ContactEnrichmentResult(success=False, source="linkedin", error="No LinkedIn URL provided")
        if not self.profile_phantom_id:
            return ContactEnrichmentResult(success=False, source="linkedin", error="No profile phantom ID configured")
        try:
            container_id = self._launch_phantom(self.profile_phantom_id, {"spreadsheetUrl": linkedin_url})
            if not container_id:
                return ContactEnrichmentResult(success=False, source="linkedin", error="Failed to launch profile phantom")
            output = self._poll_results(container_id)
            if not output:
                return ContactEnrichmentResult(success=False, source="linkedin", error="Profile phantom returned no results")
            linkedin_context = self._parse_profile_results(output)
            if not linkedin_context:
                return ContactEnrichmentResult(
                    success=False,
                    source="linkedin",
                    error="Could not extract LinkedIn context from profile phantom output",
                )
            contact = Contact(linkedin_url=linkedin_url, linkedin_context=linkedin_context, enrichment_sources=["linkedin"])
            return ContactEnrichmentResult(
                success=True,
                contact=contact,
                source="linkedin",
                fields_enriched=["linkedin_context"],
                raw_response=output if isinstance(output, dict) else {"raw": str(output)},
            )
        except Exception as exc:
            return ContactEnrichmentResult(success=False, source="linkedin", error=str(exc))

    def _launch_phantom(self, phantom_id: str, arguments: dict) -> Optional[str]:
        try:
            response = self._client.post(f"{PHANTOMBUSTER_API_BASE}/agents/launch", json={"id": phantom_id, "argument": arguments})
            response.raise_for_status()
            return response.json().get("containerId")
        except Exception:
            return None

    def _poll_results(self, container_id: str) -> Optional[dict]:
        start_time = time.time()
        while (time.time() - start_time) < self.poll_timeout:
            try:
                response = self._client.get(
                    f"{PHANTOMBUSTER_API_BASE}/containers/fetch-output",
                    params={"id": container_id},
                )
                response.raise_for_status()
                data = response.json()
                status = data.get("status")
                if status == "finished":
                    output = data.get("output")
                    if output:
                        return output if isinstance(output, dict) else {"raw": output}
                    result_obj = data.get("resultObject")
                    if result_obj:
                        return result_obj if isinstance(result_obj, dict) else {"raw": result_obj}
                    return data
                if status in ("error", "launch error"):
                    return None
                time.sleep(self.poll_interval)
            except Exception:
                return None
        return None

    def _parse_profile_results(self, output: dict) -> Optional[str]:
        parts = []
        data = output
        if "raw" in output and isinstance(output["raw"], str):
            try:
                parsed = json.loads(output["raw"])
                data = parsed[0] if isinstance(parsed, list) and parsed else parsed
            except (json.JSONDecodeError, IndexError):
                return output["raw"][:500] if output["raw"] else None
        if isinstance(data, list) and data:
            data = data[0]
        if not isinstance(data, dict):
            return str(data)[:500] if data else None
        headline = data.get("headline") or data.get("title")
        if headline:
            parts.append(f"Headline: {headline}")
        summary = data.get("summary") or data.get("about") or data.get("description")
        if summary:
            parts.append(f"About: {summary[:300]}")
        current_job = data.get("currentJob") or data.get("occupation")
        if current_job:
            parts.append(f"Current role: {current_job}")
        posts = data.get("posts") or data.get("activities") or data.get("recentPosts")
        if posts and isinstance(posts, list):
            post_texts = []
            for post in posts[:3]:
                if isinstance(post, dict):
                    text = post.get("text") or post.get("content") or post.get("postContent")
                    if text:
                        post_texts.append(text[:200])
                elif isinstance(post, str):
                    post_texts.append(post[:200])
            if post_texts:
                parts.append("Recent posts: " + " | ".join(post_texts))
        skills = data.get("skills")
        if skills and isinstance(skills, list):
            skill_names = [skill.get("name", str(skill)) if isinstance(skill, dict) else str(skill) for skill in skills[:5]]
            parts.append(f"Skills: {', '.join(skill_names)}")
        return " | ".join(parts) if parts else None

    def _parse_company_results(self, output: dict) -> Optional[str]:
        parts = []
        data = output
        if "raw" in output and isinstance(output["raw"], str):
            try:
                parsed = json.loads(output["raw"])
                data = parsed[0] if isinstance(parsed, list) and parsed else parsed
            except (json.JSONDecodeError, IndexError):
                return output["raw"][:500] if output["raw"] else None
        if isinstance(data, list) and data:
            data = data[0]
        if not isinstance(data, dict):
            return str(data)[:500] if data else None
        description = data.get("description") or data.get("tagline") or data.get("about")
        if description:
            parts.append(f"About: {description[:300]}")
        specialties = data.get("specialties") or data.get("specialities")
        if specialties:
            if isinstance(specialties, list):
                parts.append(f"Specialties: {', '.join(specialties[:5])}")
            elif isinstance(specialties, str):
                parts.append(f"Specialties: {specialties[:200]}")
        posts = data.get("posts") or data.get("updates") or data.get("recentPosts")
        if posts and isinstance(posts, list):
            post_texts = []
            for post in posts[:3]:
                if isinstance(post, dict):
                    text = post.get("text") or post.get("content") or post.get("postContent")
                    if text:
                        post_texts.append(text[:200])
                elif isinstance(post, str):
                    post_texts.append(post[:200])
            if post_texts:
                parts.append("Recent updates: " + " | ".join(post_texts))
        employee_count = data.get("employeeCount") or data.get("staffCount")
        if employee_count:
            parts.append(f"LinkedIn employees: {employee_count}")
        follower_count = data.get("followerCount") or data.get("followersCount")
        if follower_count:
            parts.append(f"Followers: {follower_count}")
        return " | ".join(parts) if parts else None
