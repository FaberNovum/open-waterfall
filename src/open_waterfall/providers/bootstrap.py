from __future__ import annotations

import os
from typing import Optional

from open_waterfall.core.config.schema import OpenWaterfallConfig
from open_waterfall.core.providers import ProviderRegistry
from open_waterfall.providers.apollo import ApolloEnricher
from open_waterfall.providers.clearbit import ClearbitEnricher
from open_waterfall.providers.dropcontact import DropcontactEnricher
from open_waterfall.providers.hunter import HunterEnricher
from open_waterfall.providers.linkedin import LinkedInEnricher
from open_waterfall.providers.prospeo import ProspeoEnricher
from open_waterfall.providers.website import WebsiteEnricher
from open_waterfall.providers.zerobounce import ZeroBounceEnricher
from open_waterfall.providers.zoominfo import ZoomInfoEnricher


def default_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register("apollo", ApolloEnricher)
    registry.register("clearbit", ClearbitEnricher)
    registry.register("dropcontact", DropcontactEnricher)
    registry.register("hunter", HunterEnricher)
    registry.register("linkedin", LinkedInEnricher)
    registry.register("prospeo", ProspeoEnricher)
    registry.register("website", WebsiteEnricher)
    registry.register("zerobounce", ZeroBounceEnricher)
    registry.register("zoominfo", ZoomInfoEnricher)
    return registry


def get_api_key(config: OpenWaterfallConfig, provider: str) -> str:
    key = config.providers.api_keys.get(provider, "")
    if key and not str(key).startswith("${"):
        return key
    return os.environ.get(f"{provider.upper()}_API_KEY", "")


def build_enrichers(config: OpenWaterfallConfig) -> tuple[list, list]:
    company_enrichers = []
    contact_enrichers = []
    registry = default_provider_registry()
    provider_settings = config.providers.settings or {}

    linkedin_instance: Optional[LinkedInEnricher] = None

    for provider in config.providers.company_waterfall:
        if provider == "website":
            openai_key = get_api_key(config, "openai")
            if not openai_key:
                continue
            settings = provider_settings.get("website", {})
            company_enrichers.append(
                registry.create(
                    "website",
                    api_key="",
                    openai_api_key=openai_key,
                    model=settings.get("model", config.research.ai.model),
                    max_pages=settings.get("max_pages", 5),
                    timeout=settings.get("timeout", 15.0),
                )
            )
            continue

        if provider == "linkedin":
            phantombuster_key = get_api_key(config, "phantombuster")
            settings = provider_settings.get("linkedin", {})
            if not phantombuster_key or not settings.get("company_phantom_id"):
                continue
            linkedin_instance = linkedin_instance or registry.create(
                "linkedin",
                api_key=phantombuster_key,
                profile_phantom_id=settings.get("profile_phantom_id", ""),
                company_phantom_id=settings.get("company_phantom_id", ""),
                poll_interval=settings.get("poll_interval", 5.0),
                poll_timeout=settings.get("poll_timeout", 120.0),
            )
            company_enrichers.append(linkedin_instance)
            continue

        api_key = get_api_key(config, provider)
        if not api_key:
            continue
        company_enrichers.append(registry.create(provider, api_key=api_key))

    for provider in config.providers.contact_waterfall:
        if provider == "linkedin":
            phantombuster_key = get_api_key(config, "phantombuster")
            settings = provider_settings.get("linkedin", {})
            if not phantombuster_key or not settings.get("profile_phantom_id"):
                continue
            linkedin_instance = linkedin_instance or registry.create(
                "linkedin",
                api_key=phantombuster_key,
                profile_phantom_id=settings.get("profile_phantom_id", ""),
                company_phantom_id=settings.get("company_phantom_id", ""),
                poll_interval=settings.get("poll_interval", 5.0),
                poll_timeout=settings.get("poll_timeout", 120.0),
            )
            contact_enrichers.append(linkedin_instance)
            continue

        if provider == "website":
            continue

        api_key = get_api_key(config, provider)
        if not api_key:
            continue
        contact_enrichers.append(registry.create(provider, api_key=api_key))

    return company_enrichers, contact_enrichers
