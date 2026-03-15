from open_waterfall.core.config.schema import OpenWaterfallConfig
from open_waterfall.providers import build_enrichers, default_provider_registry


def test_default_provider_registry_contains_core_names() -> None:
    registry = default_provider_registry()

    assert "apollo" in registry.registered_names()
    assert "hunter" in registry.registered_names()
    assert "website" in registry.registered_names()


def test_build_enrichers_skips_missing_api_keys() -> None:
    config = OpenWaterfallConfig.model_validate(
        {
            "providers": {
                "company_waterfall": ["apollo", "website"],
                "contact_waterfall": ["hunter"],
                "api_keys": {},
                "settings": {},
            }
        }
    )

    company_enrichers, contact_enrichers = build_enrichers(config)

    assert company_enrichers == []
    assert contact_enrichers == []

