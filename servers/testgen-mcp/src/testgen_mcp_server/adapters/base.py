"""Adapter contract: the interface every language adapter implements.

This module is the pinned contract shared by the spec store, the engine, and
each concrete adapter. Keep it dependency-free (stdlib only) and stable — other
modules import these types directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Symbol:
    """A testable top-level symbol (function or method) in a source file.

    start_line / end_line are 1-based, inclusive, spanning the full declaration
    (signature through closing brace) so coverage line ranges can be intersected
    against them.
    """

    name: str
    kind: str  # "func" | "method"
    receiver: str | None  # e.g. "*mlapi" for a method; None for a plain func
    start_line: int
    end_line: int


@dataclass
class FileCoverage:
    """Aggregated coverage for one source file, parsed from a coverage artifact."""

    source_rel: str  # repo-relative source path
    covered_stmts: int
    total_stmts: int
    covered_lines: set[int] = field(default_factory=set)
    uncovered_lines: set[int] = field(default_factory=set)

    @property
    def percent(self) -> float:
        """Statement coverage percentage in [0, 100]; 100.0 when there are no statements."""
        if self.total_stmts <= 0:
            return 100.0
        return round(100.0 * self.covered_stmts / self.total_stmts, 2)


@runtime_checkable
class LanguageAdapter(Protocol):
    """Per-language conventions. All paths are repo-relative POSIX strings.

    Implementations MUST be pure/deterministic and read no global state beyond
    what is passed in — the engine owns filesystem access and passes source text
    and repo roots explicitly where needed.
    """

    #: Short language id, e.g. "go", "typescript".
    name: str

    def handles(self, source_rel: str) -> bool:
        """True if this adapter is responsible for the given source path (by extension)."""
        ...

    def is_test_file(self, source_rel: str) -> bool:
        """True if the path is itself a test file (e.g. *_test.go, *.test.ts)."""
        ...

    def is_generated(self, source_rel: str, source_text: str) -> bool:
        """True if the file is generated / must-not-edit (header marker or known dir)."""
        ...

    def list_symbols(self, source_text: str) -> list[Symbol]:
        """Return the testable top-level symbols declared in the file."""
        ...

    def extract_symbol_sources(self, source_text: str) -> dict[str, str]:
        """Map symbol name -> its exact source text (signature + body).

        Used to compute a symbol-scoped fingerprint so unrelated edits elsewhere
        in the file do not churn the spec's freshness.
        """
        ...

    def test_path(self, source_rel: str) -> str:
        """Return the conventional test-file path for a source file."""
        ...

    def test_command(self, package_rel: str) -> str:
        """Command to run the package's unit tests (run on build machine / CI)."""
        ...

    def coverage_command(self, package_rel: str) -> str:
        """Command to run the package's tests with coverage output."""
        ...

    def parse_coverage(self, raw: str) -> list[FileCoverage]:
        """Parse a raw coverage artifact into per-file coverage."""
        ...

    def reference_tests(self, repo_root: str, package_rel: str) -> list[str]:
        """Return repo-relative paths of golden example test files to mimic style."""
        ...
