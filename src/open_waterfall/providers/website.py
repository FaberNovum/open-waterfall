from __future__ import annotations

import json
import re
from typing import Optional
from urllib.parse import urljoin

import httpx
from openai import OpenAI

from open_waterfall.core.models.company import Company, CompanyEnrichmentResult
from open_waterfall.core.models.contact import ContactEnrichmentResult
from open_waterfall.core.providers.base import BaseEnricher


PAGES_TO_TRY = [
    "/",
    "/about",
    "/about-us",
    "/company",
    "/sustainability",
    "/esg",
    "/corporate-responsibility",
    "/investor-relations",
    "/investors",
    "/annual-report",
]

EXTRACTION_PROMPT = """You are a B2B research analyst. Given the raw text content from a company's website pages, extract structured information.

Company domain: {domain}

Website content:
{content}

Extract the following into a JSON object. Use null for any field you cannot determine:

{{
  "name": "Official company name",
  "industry": "Primary industry",
  "description": "2-3 sentence company description",
  "employee_count": 12345,
  "revenue": 1500000000,
  "headquarters_city": "City",
  "headquarters_state": "State/Province",
  "headquarters_country": "Country",
  "founded_year": 1990,
  "website_context": "Specific useful company context for messaging or research",
  "linkedin_url": "LinkedIn company page URL if found"
}}

Return ONLY the JSON object."""


class WebsiteEnricher(BaseEnricher):
    name = "website"
    base_url = ""

    def __init__(
        self,
        api_key: str,
        openai_api_key: str,
        model: str = "gpt-4.1-mini",
        max_pages: int = 5,
        timeout: float = 15.0,
    ):
        super().__init__(api_key=api_key, timeout=timeout)
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.model = model
        self.max_pages = max_pages
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            follow_redirects=True,
        )

    def enrich_company(self, domain: str) -> CompanyEnrichmentResult:
        try:
            page_contents = self._fetch_pages(domain)
            if not page_contents:
                return CompanyEnrichmentResult(
                    success=False,
                    source="website",
                    error=f"Could not fetch any pages from {domain}",
                )
            extracted = self._extract_with_llm(domain, self._combine_content(page_contents))
            if not extracted:
                return CompanyEnrichmentResult(success=False, source="website", error="LLM extraction returned no data")
            company = self._build_company(domain, extracted)
            fields_enriched = [key for key, value in extracted.items() if value not in (None, "", 0)]
            return CompanyEnrichmentResult(
                success=True,
                company=company,
                source="website",
                fields_enriched=fields_enriched,
                raw_response=extracted,
            )
        except Exception as exc:
            return CompanyEnrichmentResult(success=False, source="website", error=str(exc))

    def enrich_contact(
        self,
        first_name: str,
        last_name: str,
        domain: str,
        company_name: Optional[str] = None,
    ) -> ContactEnrichmentResult:
        return ContactEnrichmentResult(
            success=False,
            source="website",
            error="Website enricher only supports company enrichment",
        )

    def _fetch_pages(self, domain: str) -> dict[str, str]:
        base_url = f"https://{domain}"
        pages: dict[str, str] = {}
        fetched = 0
        for path in PAGES_TO_TRY:
            if fetched >= self.max_pages:
                break
            try:
                response = self.client.get(urljoin(base_url, path))
                if response.status_code != 200:
                    continue
                text = self._extract_text(response.text)
                if text and len(text) > 100:
                    pages[path] = text
                    fetched += 1
            except Exception:
                continue
        return pages

    def _extract_text(self, html: str) -> str:
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
        return re.sub(r"\s+", " ", text).strip()

    def _combine_content(self, pages: dict[str, str], max_chars: int = 12000) -> str:
        sections = []
        remaining = max_chars
        for path, content in pages.items():
            header = f"\n--- Page: {path} ---\n"
            available = remaining - len(header)
            if available <= 0:
                break
            truncated = content[:available]
            sections.append(header + truncated)
            remaining -= len(header) + len(truncated)
        return "\n".join(sections)

    def _extract_with_llm(self, domain: str, content: str) -> Optional[dict]:
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise B2B research analyst. Return only valid JSON."},
                    {"role": "user", "content": EXTRACTION_PROMPT.format(domain=domain, content=content)},
                ],
                max_tokens=1200,
                temperature=0.2,
            )
            content_text = response.choices[0].message.content.strip()
            if content_text.startswith("```"):
                content_text = content_text.split("\n", 1)[1]
                if content_text.endswith("```"):
                    content_text = content_text[:-3]
                content_text = content_text.strip()
            return json.loads(content_text)
        except Exception:
            return None

    def _build_company(self, domain: str, data: dict) -> Company:
        return Company(
            domain=domain,
            name=data.get("name"),
            industry=data.get("industry"),
            description=data.get("description"),
            employee_count=data.get("employee_count"),
            revenue=data.get("revenue"),
            headquarters_city=data.get("headquarters_city"),
            headquarters_state=data.get("headquarters_state"),
            headquarters_country=data.get("headquarters_country"),
            founded_year=data.get("founded_year"),
            linkedin_url=data.get("linkedin_url"),
            website_context=data.get("website_context"),
            enrichment_sources=["website"],
        )
