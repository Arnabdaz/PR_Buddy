"""Engine core: filesystem I/O, gap detection, and spec operations.

All source paths are repo-relative POSIX strings.  This module owns filesystem
access so that callers (tools, tests) operate at a higher level.  The layer
above (tools.py) is a thin MCP wrapper; this module contains all non-trivial
logic.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from testgen_mcp_server import spec_schema, specstore
from testgen_mcp_server.adapters.base import FileCoverage, LanguageAdapter
from testgen_mcp_server.adapters.go import GoAdapter
from testgen_mcp_server.adapters.registry import adapter_for
from testgen_mcp_server.config import get_config

# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------


def _abs(rel: str) -> Path:
    """Return the absolute path by joining *repo_root* with *rel*."""
    return get_config().repo_root / rel


def read_source(source_rel: str) -> str | None:
    """Return the text of *source_rel*, or ``None`` if the file does not exist."""
    p = _abs(source_rel)
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Fingerprinting
# ---------------------------------------------------------------------------


def current_fingerprint(source_rel: str) -> str | None:
    """Compute the symbol-scoped fingerprint for the current state of *source_rel*.

    Returns ``None`` if the file is unsupported (no adapter) or missing.
    """
    adapter = adapter_for(source_rel)
    if adapter is None:
        return None
    text = read_source(source_rel)
    if text is None:
        return None
    return specstore.fingerprint(adapter.extract_symbol_sources(text))


# ---------------------------------------------------------------------------
# Path mapping
# ---------------------------------------------------------------------------


def paths_for(source_rel: str) -> dict[str, str]:
    """Return a dict with ``source``, ``test_path``, and ``spec_path`` keys.

    Raises :class:`ValueError` if no adapter handles the file type.
    """
    adapter = adapter_for(source_rel)
    if adapter is None:
        msg = f"unsupported file type: {source_rel}"
        raise ValueError(msg)
    return {
        "source": source_rel,
        "test_path": adapter.test_path(source_rel),
        "spec_path": specstore.spec_rel_path(source_rel),
    }


# ---------------------------------------------------------------------------
# Freshness
# ---------------------------------------------------------------------------


def spec_freshness(source_rel: str) -> str:
    """Return ``"missing"``, ``"fresh"``, or ``"stale"`` for *source_rel*'s spec."""
    return specstore.freshness(source_rel, current_fingerprint(source_rel) or "")


# ---------------------------------------------------------------------------
# Coverage loading
# ---------------------------------------------------------------------------


def _load_coverage() -> dict[str, FileCoverage]:
    """Glob ``coverage_dir`` for ``*.coverprofile`` / ``*.out`` files and parse them.

    Returns a ``dict`` keyed by :attr:`FileCoverage.source_rel` (last file wins
    on collision).  Best-effort: unreadable or malformed files are silently
    skipped.  Returns ``{}`` if the coverage directory does not exist.
    """
    cfg = get_config()
    coverage_root = cfg.repo_root / cfg.coverage_dir
    if not coverage_root.exists():
        return {}

    go_adapter = GoAdapter()
    result: dict[str, FileCoverage] = {}

    for pattern in ("*.coverprofile", "*.out"):
        for path in coverage_root.rglob(pattern):
            try:
                raw = path.read_text(encoding="utf-8")
                for fc in go_adapter.parse_coverage(raw):
                    result[fc.source_rel] = fc
            except Exception:  # noqa: S112,PERF203
                continue

    return result


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------


def _resolve_targets(target: str) -> list[str]:
    """Expand *target* into a sorted list of repo-relative source file paths.

    Resolution order:

    1. Directory → walk recursively; keep files whose adapter is not ``None``,
       that are not test files, and that are not generated.
    2. Single file path → ``[target]``.
    3. Comma / whitespace-separated list → split, keep entries that exist as
       files.
    4. Otherwise → raise :class:`ValueError`.
    """
    abs_target = _abs(target)

    if abs_target.is_dir():
        repo_root = get_config().repo_root
        candidates: list[str] = []
        for full in sorted(abs_target.rglob("*")):
            if not full.is_file():
                continue
            rel = full.relative_to(repo_root).as_posix()
            adapter = adapter_for(rel)
            if adapter is None:
                continue
            if adapter.is_test_file(rel):
                continue
            try:
                text = full.read_text(encoding="utf-8")
            except Exception:  # noqa: S112
                continue
            if adapter.is_generated(rel, text):
                continue
            candidates.append(rel)
        return sorted(candidates)

    if abs_target.is_file():
        return [target]

    # Comma- or whitespace-separated list
    parts = [p.strip() for p in re.split(r"[,\s]+", target) if p.strip()]
    files = [p for p in parts if _abs(p).is_file()]
    if files:
        return files

    msg = f"target not found: {target}"
    raise ValueError(msg)


# ---------------------------------------------------------------------------
# Gap detection
# ---------------------------------------------------------------------------


def detect_gaps(target: str) -> dict[str, Any]:
    """Scan *target* for test and spec coverage gaps.

    Returns a dict with keys:

    - ``"target"``: the original *target* string.
    - ``"files"``: list of per-file record dicts (see below).
    - ``"summary"``: aggregate counts (``total``, ``missing_spec``,
      ``stale_spec``, ``no_test``).

    Each file record contains: ``source``, ``language``, ``test_path``,
    ``spec_path``, ``has_test`` (bool), ``has_spec`` (bool),
    ``spec_freshness`` (``"missing"``/``"fresh"``/``"stale"``),
    ``coverage_percent`` (float or ``None``), ``symbols`` (list[str]),
    and ``recommendation``.
    """
    sources = _resolve_targets(target)
    coverage_map = _load_coverage()

    files: list[dict[str, Any]] = []
    missing_spec_count = 0
    stale_spec_count = 0
    no_test_count = 0

    for rel in sources:
        adapter = adapter_for(rel)
        if adapter is None:
            continue

        try:
            text = read_source(rel)
            if text is None:
                continue

            test_rel = adapter.test_path(rel)
            has_test = _abs(test_rel).exists()
            has_spec = specstore.read_spec(rel) is not None
            freshness_val = spec_freshness(rel)

            fc = coverage_map.get(rel)
            coverage_percent: float | None = fc.percent if fc is not None else None

            symbols = [s.name for s in adapter.list_symbols(text)]

            if freshness_val == "fresh":
                recommendation = "reuse_spec"
            elif freshness_val == "stale":
                recommendation = "update_spec"
                stale_spec_count += 1
            elif has_test:
                recommendation = "derive_spec_from_tests"
                missing_spec_count += 1
            else:
                recommendation = "write_spec_from_code"
                missing_spec_count += 1

            if not has_test:
                no_test_count += 1

            files.append(
                {
                    "source": rel,
                    "language": adapter.name,
                    "test_path": test_rel,
                    "spec_path": specstore.spec_rel_path(rel),
                    "has_test": has_test,
                    "has_spec": has_spec,
                    "spec_freshness": freshness_val,
                    "coverage_percent": coverage_percent,
                    "symbols": symbols,
                    "recommendation": recommendation,
                }
            )

        except Exception:  # noqa: S112
            continue

    summary = {
        "total": len(files),
        "missing_spec": missing_spec_count,
        "stale_spec": stale_spec_count,
        "no_test": no_test_count,
    }

    return {"target": target, "files": files, "summary": summary}


# ---------------------------------------------------------------------------
# Spec writing
# ---------------------------------------------------------------------------


def write_spec(
    source_rel: str,
    body: str,
    symbols: list[str],
    generated_from: str,
    status: str,
) -> str:
    """Compute the current fingerprint and write the spec for *source_rel*.

    Raises :class:`ValueError` if the file is missing, unsupported, or the
    body does not satisfy the required per-symbol structure.  The error
    message lists every problem and names the two helper functions that can
    assist in fixing them.

    Returns the repo-relative spec path.
    """
    fp = current_fingerprint(source_rel)
    if fp is None:
        msg = f"unsupported or missing file: {source_rel}"
        raise ValueError(msg)

    problems = spec_schema.validate(body, symbols)
    if problems:
        msg = (
            "spec does not meet the required structure — fix and retry:\n- "
            + "\n- ".join(problems)
            + "\nCall spec_template() for a skeleton or validate_spec() to pre-check."
        )
        raise ValueError(msg)

    return specstore.write_spec(
        source_rel=source_rel,
        body=body,
        symbols=symbols,
        code_fingerprint=fp,
        generated_from=generated_from,
        status=status,
        spec_schema_version=spec_schema.SPEC_SCHEMA_VERSION,
    )


def spec_template(source_rel: str, symbols: list[str] | None = None) -> str:
    """Return a fill-in-the-blanks spec skeleton for *source_rel*.

    If *symbols* is ``None``, the list is derived from the source file via
    the language adapter.  Raises :class:`ValueError` if the file type is
    unsupported or the source file does not exist.
    """
    adapter = adapter_for(source_rel)
    if adapter is None:
        msg = f"unsupported file type: {source_rel}"
        raise ValueError(msg)
    text = read_source(source_rel)
    if text is None:
        msg = f"source file not found: {source_rel}"
        raise ValueError(msg)
    if symbols is None:
        symbols = [s.name for s in adapter.list_symbols(text)]
    return spec_schema.render_template(source_rel, symbols)


def validate_spec(
    source_rel: str,
    body: str,
    symbols: list[str] | None = None,
) -> list[str]:
    """Validate *body*'s structure for *source_rel*.

    If *symbols* is ``None``, the list is derived from the source file via
    the language adapter.  Raises :class:`ValueError` if the file type is
    unsupported or the source file does not exist.

    Returns a list of problem strings (empty = valid).
    """
    if symbols is None:
        adapter = adapter_for(source_rel)
        if adapter is None:
            msg = f"unsupported file type: {source_rel}"
            raise ValueError(msg)
        text = read_source(source_rel)
        if text is None:
            msg = f"source file not found: {source_rel}"
            raise ValueError(msg)
        symbols = [s.name for s in adapter.list_symbols(text)]
    return spec_schema.validate(body, symbols)


# ---------------------------------------------------------------------------
# Package-level helpers
# ---------------------------------------------------------------------------


def _adapter_for_package(package_rel: str) -> LanguageAdapter:
    """Return the adapter for the first handled source file found in *package_rel*.

    Falls back to :class:`GoAdapter` if the directory is missing or contains no
    recognised source files.
    """
    pkg_dir = _abs(package_rel)
    if pkg_dir.is_dir():
        for path in sorted(pkg_dir.iterdir()):
            if path.is_file():
                rel = path.relative_to(get_config().repo_root).as_posix()
                adapter = adapter_for(rel)
                if adapter is not None:
                    return adapter
    return GoAdapter()


def reference_tests_for(package_rel: str) -> list[str]:
    """Return repo-relative paths of reference test files for *package_rel*."""
    adapter = _adapter_for_package(package_rel)
    return adapter.reference_tests(str(get_config().repo_root), package_rel)


def commands_for(package_rel: str) -> dict[str, str]:
    """Return the test and coverage commands for *package_rel*."""
    adapter = _adapter_for_package(package_rel)
    pkg = package_rel.strip("/")
    return {
        "test": adapter.test_command(pkg),
        "coverage": adapter.coverage_command(pkg),
    }
