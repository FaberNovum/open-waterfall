from __future__ import annotations

from open_waterfall.core.config.schema import OpenWaterfallConfig
from open_waterfall.research.base import ResearchModule
from open_waterfall.research.contact_summary import ContactSummaryResearch
from open_waterfall.research.trigger_detection import TriggerDetectionResearch
from open_waterfall.research.website_context import WebsiteContextResearch


def build_research_modules(config: OpenWaterfallConfig) -> list[ResearchModule]:
    module_map = {
        "contact_summary": ContactSummaryResearch,
        "trigger_detection": TriggerDetectionResearch,
        "website_context": WebsiteContextResearch,
    }
    modules: list[ResearchModule] = []
    for name in config.research.enabled_modules:
        module_cls = module_map.get(name)
        if module_cls:
            modules.append(module_cls())
    return modules

