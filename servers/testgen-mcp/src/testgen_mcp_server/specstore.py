"""Spec store: file I/O, path mapping, fingerprinting, and freshness checks.

This module is adapter-free — it only deals with file-system operations and
content hashing.  Language adapters in ``adapters/`` are never imported here.
"""

from __future__ import annotations

import datetime
import hashlib
from dataclasses import dataclass
from pathlib import PurePosixPath

from testgen_mcp_server.config import get_config
from testgen_mcp_server.spec_schema import SPEC_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Spec:
    """A parsed spec file."""

    source: str            # repo-relative source path this spec describes
    symbols: list[str]     # symbol names covered by this spec
    code_fingerprint: str  # e.g. "sha256:abc123..."
    generated_from: str    # "scratch" | "tests" | "mixed"
    status: str            # "draft" | "approved"
    updated: str           # ISO date "YYYY-MM-DD"
    body: str              # the Markdown body AFTER the frontmatter
    spec_schema_version: int = SPEC_SCHEMA_VERSION  # schema version for structure enforcement


# ---------------------------------------------------------------------------
# Path mapping
# ---------------------------------------------------------------------------


def spec_rel_path(source_rel: str) -> str:
    """Map a repo-relative source path to its repo-relative spec path.

    Rule: ``{spec_dir}/{parent_dirs}/{stem}.spec.md`` using POSIX paths.

    Example::

        source_rel="services/api/srv/runtimes/runtimes.go", spec_dir="testspecs"
        -> "testspecs/services/api/srv/runtimes/runtimes.spec.md"

    The stem drops the final extension only (``runtimes.go`` -> ``runtimes``).
    """
    cfg = get_config()
    p = PurePosixPath(source_rel)
    stem = p.stem  # drops the final extension only
    spec_name = f"{stem}.spec.md"
    return str(PurePosixPath(cfg.spec_dir) / p.parent / spec_name)


# ---------------------------------------------------------------------------
# Fingerprinting
# ---------------------------------------------------------------------------


def fingerprint(symbol_sources: dict[str, str]) -> str:
    """Deterministic, order-independent content hash of symbol sources.

    Sorts items by key, concatenates ``name + "\\x00" + source + "\\x00"`` for
    each entry, SHA-256s the result, and returns ``"sha256:" + hexdigest``.
    An empty dict returns a stable hash of the empty byte sequence.
    """
    h = hashlib.sha256()
    for key in sorted(symbol_sources):
        h.update((key + "\x00" + symbol_sources[key] + "\x00").encode())
    return f"sha256:{h.hexdigest()}"


# ---------------------------------------------------------------------------
# Frontmatter helpers (hand-rolled — no yaml dependency)
# ---------------------------------------------------------------------------


def _strip_quotes(value: str) -> str:
    """Strip a single pair of matching surrounding quotes ('' or \"\")."""
    if len(value) >= 2 and (
        (value[0] == '"' and value[-1] == '"')
        or (value[0] == "'" and value[-1] == "'")
    ):
        return value[1:-1]
    return value


def _parse_symbols(raw: str) -> list[str]:
    """Parse an inline list ``[a, b, c]`` into a Python list of strings."""
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        return [_strip_quotes(s.strip()) for s in inner.split(",") if s.strip()]
    return []


def _parse_frontmatter(content: str) -> tuple[dict[str, str | list[str]], str]:
    """Parse frontmatter + body from a spec file.

    Returns ``(fields, body)``.  If the file has no valid frontmatter,
    ``fields`` is empty and ``body`` is the full ``content``.
    """
    lines = content.split("\n")

    if not lines or lines[0].rstrip("\r") != "---":
        return {}, content

    # Locate the closing ---
    end_idx: int | None = None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r") == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}, content

    fields: dict[str, str | list[str]] = {}
    for line in lines[1:end_idx]:
        if ": " in line:
            key, _, raw_value = line.partition(": ")
            key = key.strip()
            raw_value = raw_value.strip()
            if key == "symbols":
                fields[key] = _parse_symbols(raw_value)
            else:
                fields[key] = _strip_quotes(raw_value)

    # Body: everything after the closing ---; strip one leading newline.
    raw_body = "\n".join(lines[end_idx + 1 :])
    if raw_body.startswith("\n"):
        raw_body = raw_body[1:]

    return fields, raw_body


def _dump_frontmatter(
    source: str,
    symbols: list[str],
    code_fingerprint: str,
    generated_from: str,
    status: str,
    updated: str,
    spec_schema_version: int = SPEC_SCHEMA_VERSION,
) -> str:
    """Render spec frontmatter to a string (including both ``---`` delimiters)."""
    symbols_str = "[" + ", ".join(symbols) + "]"
    return (
        "---\n"
        f"source: {source}\n"
        f"symbols: {symbols_str}\n"
        f"code_fingerprint: {code_fingerprint}\n"
        f"generated_from: {generated_from}\n"
        f"status: {status}\n"
        f"updated: {updated}\n"
        f"spec_schema_version: {spec_schema_version}\n"
        "---\n"
    )


def _field_str(fields: dict[str, str | list[str]], key: str) -> str:
    """Extract a string field, returning '' when absent or wrong type."""
    v = fields.get(key, "")
    return v if isinstance(v, str) else ""


def _field_list(fields: dict[str, str | list[str]], key: str) -> list[str]:
    """Extract a list field, returning [] when absent or wrong type."""
    v = fields.get(key, [])
    return v if isinstance(v, list) else []


def _field_int(
    fields: dict[str, str | list[str]],
    key: str,
    default: int = 1,
) -> int:
    """Extract an integer field, returning *default* when absent or unparseable."""
    v = fields.get(key, "")
    if isinstance(v, str) and v:
        try:
            return int(v)
        except ValueError:
            return default
    return default


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def read_spec(source_rel: str) -> Spec | None:
    """Load and parse the spec for *source_rel*.

    Returns ``None`` if the spec file does not exist.
    """
    cfg = get_config()
    spec_path = cfg.repo_root / spec_rel_path(source_rel)
    if not spec_path.exists():
        return None

    content = spec_path.read_text(encoding="utf-8")
    fields, body = _parse_frontmatter(content)

    return Spec(
        source=_field_str(fields, "source"),
        symbols=_field_list(fields, "symbols"),
        code_fingerprint=_field_str(fields, "code_fingerprint"),
        generated_from=_field_str(fields, "generated_from"),
        status=_field_str(fields, "status"),
        updated=_field_str(fields, "updated"),
        body=body,
        spec_schema_version=_field_int(fields, "spec_schema_version", default=1),
    )


def write_spec(
    source_rel: str,
    body: str,
    symbols: list[str],
    code_fingerprint: str,
    generated_from: str,
    status: str,
    updated: str | None = None,
    spec_schema_version: int = SPEC_SCHEMA_VERSION,
) -> str:
    """Write (or overwrite) the spec file for *source_rel*.

    Creates parent directories as needed.  If *updated* is ``None``, today's
    date is used.  Returns the repo-relative spec path.
    """
    if updated is None:
        updated = datetime.date.today().isoformat()

    rel_path = spec_rel_path(source_rel)
    cfg = get_config()
    spec_path = cfg.repo_root / rel_path
    spec_path.parent.mkdir(parents=True, exist_ok=True)

    fm = _dump_frontmatter(
        source_rel,
        symbols,
        code_fingerprint,
        generated_from,
        status,
        updated,
        spec_schema_version=spec_schema_version,
    )
    spec_path.write_text(fm + body, encoding="utf-8")

    return rel_path


def freshness(source_rel: str, current_fingerprint: str) -> str:
    """Check whether the stored spec is up-to-date with *current_fingerprint*.

    Returns ``"missing"``, ``"fresh"``, or ``"stale"``.
    """
    spec = read_spec(source_rel)
    if spec is None:
        return "missing"
    return "fresh" if spec.code_fingerprint == current_fingerprint else "stale"
