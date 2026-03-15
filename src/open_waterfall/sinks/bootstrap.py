from __future__ import annotations

import os

from open_waterfall.core.config.schema import OpenWaterfallConfig
from open_waterfall.sinks.base import LeadSink
from open_waterfall.sinks.csv_sink import CsvSink


def _resolve_hubspot_token(config: OpenWaterfallConfig) -> str:
    token = config.sinks.hubspot.access_token or config.providers.api_keys.get("hubspot", "")
    if token:
        return token

    for env_name in ("HUBSPOT_ACCESS_TOKEN", "HUBSPOT_API_KEY"):
        if os.environ.get(env_name):
            return os.environ[env_name]

    return ""


def _build_hubspot_sink(config: OpenWaterfallConfig) -> LeadSink:
    from open_waterfall.sinks.hubspot import HubSpotCrmSink

    return HubSpotCrmSink(
        access_token=_resolve_hubspot_token(config),
        config=config.sinks.hubspot,
    )


def build_sinks(config: OpenWaterfallConfig) -> tuple[list[LeadSink], list[str]]:
    sinks: list[LeadSink] = []
    warnings: list[str] = []

    for sink_name in config.sinks.enabled:
        if sink_name == "csv":
            sinks.append(CsvSink(config.sinks.csv.get("output_path", "./output/enriched.csv")))
        elif sink_name == "hubspot":
            if not config.sinks.hubspot.enabled:
                warnings.append("hubspot sink is disabled in config; skipping")
                continue

            token = _resolve_hubspot_token(config)
            if not token:
                warnings.append("hubspot sink requires a HubSpot access token; skipping")
                continue

            try:
                sinks.append(_build_hubspot_sink(config))
            except ImportError:
                warnings.append("hubspot dependency is not installed; install open-waterfall[hubspot]")
        else:
            warnings.append(f"unknown sink '{sink_name}' skipped")

    return sinks, warnings
