"""Adapter registry: pick the right language adapter for a source path."""

from __future__ import annotations

from .base import LanguageAdapter
from .go import GoAdapter

# Ordered list of available adapters. Add TypeScriptAdapter here later.
_ADAPTERS: list[LanguageAdapter] = [GoAdapter()]


def all_adapters() -> list[LanguageAdapter]:
    """Return all registered adapters."""
    return list(_ADAPTERS)


def adapter_for(source_rel: str) -> LanguageAdapter | None:
    """Return the adapter that handles this source path, or None if unsupported."""
    for adapter in _ADAPTERS:
        if adapter.handles(source_rel):
            return adapter
    return None
