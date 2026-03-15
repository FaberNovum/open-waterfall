from __future__ import annotations

from open_waterfall.core.config.schema import OpenWaterfallConfig
from open_waterfall.providers.bootstrap import get_api_key
from open_waterfall.sourcing.apollo import ApolloLeadSource
from open_waterfall.sourcing.base import BaseLeadSource


def build_lead_source(config: OpenWaterfallConfig) -> tuple[BaseLeadSource | None, list[str]]:
    warnings: list[str] = []

    if not config.source.enabled:
        warnings.append("source stage is disabled in config")
        return None, warnings

    provider = (config.source.provider or "").strip().lower()
    if not provider:
        warnings.append("source.provider is required when source stage is enabled")
        return None, warnings

    if provider != "apollo":
        warnings.append(f"source provider '{provider}' is not supported yet")
        return None, warnings

    api_key = get_api_key(config, provider)
    if not api_key:
        warnings.append("apollo source requires APOLLO_API_KEY or providers.api_keys.apollo")
        return None, warnings

    settings = config.providers.settings.get("apollo", {})
    return ApolloLeadSource(api_key=api_key, timeout=settings.get("timeout", 30.0)), warnings
