"""Language adapters: per-language conventions behind one interface.

The engine is language-agnostic; each adapter knows how one language maps
source files to test files, lists symbols, extracts symbol source (for
fingerprinting), parses coverage, and resolves test/coverage commands.
"""

from __future__ import annotations

from .base import FileCoverage, LanguageAdapter, Symbol
from .registry import adapter_for, all_adapters

__all__ = [
    "FileCoverage",
    "LanguageAdapter",
    "Symbol",
    "adapter_for",
    "all_adapters",
]
