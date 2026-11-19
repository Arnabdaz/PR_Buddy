"""Spec schema: version, required fields, template generator, and validator.

Defines the structural contract for spec bodies — what sections and fields
*must* be present — while leaving wording entirely free.  Validation is
deliberately tolerant: it accepts multiple formatting variants and only
flags genuinely missing content so models can self-correct quickly.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Schema version and field constants
# ---------------------------------------------------------------------------

SPEC_SCHEMA_VERSION = 1

REQUIRED_FIELDS = ("Contract", "Rules", "Cases", "Test level")
OPTIONAL_FIELDS = ("Origin", "Inputs", "Out of scope")


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------


def render_template(
    source_rel: str,
    symbols: list[str],
    package_purpose: str = "",
) -> str:
    """Return a fill-in-the-blanks spec skeleton for *source_rel*.

    One ``### <name>`` block per symbol in the given order.  The caller
    fills in the ``_TODO_`` placeholders and then passes the result to
    ``write_spec``.
    """
    purpose = package_purpose or "_TODO: one line_"
    header = (
        f"# Spec: {source_rel}\n\n"
        f"**Package purpose:** {purpose}\n"
        "**Default test level:** _TODO: unit | component_\n\n"
        "## Symbols\n"
    )

    blocks: list[str] = []
    for name in symbols:
        block = (
            f"\n### {name}\n"
            "- **Origin:** _from-code | from-tests_\n"
            "- **Contract:** _TODO: one sentence — purpose + success/error return contract_\n"
            '- **Inputs:** _TODO: params → domains/boundaries, or "none"_\n'
            "- **Rules:** _source-ordered `condition → outcome` lines_\n"
            "  1. _TODO_\n"
            "- **Cases:**\n"
            "  | # | Preconditions / input | Expected |\n"
            "  |---|---|---|\n"
            "  | 1 | _TODO_ | _TODO_ |\n"
            "- **Test level & fixtures:** _unit|component_; _none|dbmocks|DryRun|gomock|k8s-fake_\n"
            "- **Out of scope:** _optional_\n"
        )
        blocks.append(block)

    return header + "".join(blocks)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _field_pattern(field_name: str) -> re.Pattern[str]:
    """Build a case-insensitive regex that matches *field_name* as a label.

    Accepts the variants:
    - ``Contract``          (bare)
    - ``Contract:``         (with colon)
    - ``**Contract**``      (Markdown bold)
    - ``**Contract:**``     (Markdown bold with colon inside)

    For "Test level", also accepts "Test level & fixtures:" and similar
    extended labels, because ``{0,2}`` trailing asterisks stop matching at
    the space after "level" so the extra text is simply ignored.
    """
    escaped = re.escape(field_name)
    return re.compile(rf"(?i)\*{{0,2}}{escaped}:?\*{{0,2}}")


def _last_component(name: str) -> str:
    """Return the final dot-separated component of a qualified symbol name.

    Example: ``mlapi.ListJobs`` -> ``ListJobs``.
    """
    return name.rsplit(".", 1)[-1]


# ---------------------------------------------------------------------------
# Public validation API
# ---------------------------------------------------------------------------


def validate(body: str, symbols: list[str]) -> list[str]:
    """Check *body* for the required per-symbol structure.

    Returns a list of human-readable problem strings.  An empty list means
    the body is structurally valid.

    Behaviour:
    * Splits *body* into per-symbol sections at lines starting with ``### ``.
    * A section "covers" a symbol if its heading *contains* the symbol name
      as a substring; the last dotted component of a qualified name is also
      tried (e.g. ``mlapi.ListJobs`` matches ``### ListJobs``).
    * For each symbol: missing section -> one problem; missing required
      fields -> one problem that lists all missing fields.
    * Does NOT validate: wording, table column names, number of cases,
      optional fields, or extra/unlisted sections.
    """
    if not symbols:
        return []

    # --- split body into sections keyed by heading text ---
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in body.splitlines():
        if line.startswith("### "):
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines)
            current_heading = line[4:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines)

    def _find_section(name: str) -> str | None:
        """Return section text for the heading that covers *name*, or None."""
        last = _last_component(name)
        for heading, text in sections.items():
            if name in heading or last in heading:
                return text
        return None

    problems: list[str] = []

    for sym in symbols:
        section_text = _find_section(sym)
        if section_text is None:
            problems.append(f"symbol '{sym}': no '### ' section found")
            continue

        missing: list[str] = [
            field
            for field in REQUIRED_FIELDS
            if not _field_pattern(field).search(section_text)
        ]
        if missing:
            problems.append(
                f"symbol '{sym}': missing field(s): {', '.join(missing)}"
            )

    return problems


def is_valid(body: str, symbols: list[str]) -> bool:
    """Return ``True`` iff ``validate(body, symbols)`` reports no problems."""
    return not validate(body, symbols)
