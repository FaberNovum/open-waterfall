from __future__ import annotations

import os

from open_waterfall.core.config.schema import OpenWaterfallConfig
from open_waterfall.messaging.cold_email_sequence import ColdEmailSequenceStrategy
from open_waterfall.messaging.linkedin_message import LinkedInMessageStrategy


def build_message_strategies(config: OpenWaterfallConfig) -> tuple[ColdEmailSequenceStrategy, LinkedInMessageStrategy]:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    email_strategy = ColdEmailSequenceStrategy(
        api_key=api_key,
        model=config.messaging.ai.model,
        temperature=config.messaging.ai.temperature,
    )
    linkedin_strategy = LinkedInMessageStrategy(
        api_key=api_key,
        model=config.messaging.ai.model,
        temperature=config.messaging.ai.temperature,
    )
    return email_strategy, linkedin_strategy

