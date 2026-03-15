from __future__ import annotations

from collections.abc import Callable

from open_waterfall.core.providers.base import BaseEnricher


class ProviderRegistry:
    """Simple provider factory registry."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[..., BaseEnricher]] = {}

    def register(self, name: str, factory: Callable[..., BaseEnricher]) -> None:
        self._factories[name] = factory

    def create(self, name: str, **kwargs) -> BaseEnricher:
        if name not in self._factories:
            raise KeyError(f"Provider '{name}' is not registered")
        return self._factories[name](**kwargs)

    def registered_names(self) -> list[str]:
        return sorted(self._factories.keys())

