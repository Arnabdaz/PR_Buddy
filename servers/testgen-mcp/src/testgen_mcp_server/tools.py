"""MCP tool definitions for the testgen-mcp server.

These are thin wrappers over :mod:`testgen_mcp_server.engine.core`.  Each tool
returns either ``{"result": "<markdown>"}`` on success or
``{"error": "<message>"}`` on failure — the same convention used by the other
PR-Buddy MCP servers.

Read-only tools are annotated with ``ToolAnnotations(readOnlyHint=True)``.
The ``write_spec`` tool is the only one that modifies filesystem state.
"""

from __future__ import annotations

from typing import Any

from mcp.types import ToolAnnotations

from . import specstore
from .app import mcp
from .engine import core

_READ_ONLY = ToolAnnotations(readOnlyHint=True)


# ---------------------------------------------------------------------------
# detect_gaps
# ---------------------------------------------------------------------------


@mcp.tool(annotations=_READ_ONLY)
def detect_gaps(target: str) -> dict[str, Any]:
    """
    Scan a target path for test and spec coverage gaps.

    target: a repo-relative directory (walks recursively), a single repo-relative
    source file path, or a comma/whitespace-separated list of file paths.

    Returns a Markdown summary with:
    - Aggregate counts (total files, missing specs, stale specs, no-test files).
    - A per-file table: source, language, has_test, spec_freshness,
      coverage %, and recommendation.
    - A compact symbol list for each file.

    Recommendations:
    - "reuse_spec"             — spec is fresh, no action needed.
    - "update_spec"            — spec is stale (code changed since last write).
    - "derive_spec_from_tests" — no spec yet, but a test file exists.
    - "write_spec_from_code"   — no spec and no test file.
    """
    try:
        result = core.detect_gaps(target)
        files = result["files"]
        summary = result["summary"]

        lines: list[str] = [
            f"# Gap Detection: `{target}`",
            "",
            "## Summary",
            f"- **Total files:** {summary['total']}",
            f"- **Missing spec:** {summary['missing_spec']}",
            f"- **Stale spec:** {summary['stale_spec']}",
            f"- **No test file:** {summary['no_test']}",
            "",
        ]

        if not files:
            lines.append("*No source files found matching the target.*")
            return {"result": "\n".join(lines)}

        lines += [
            "## Files",
            "",
            "| Source | Language | Has Test | Spec Freshness | Coverage % | Recommendation |",
            "|--------|----------|----------|----------------|------------|----------------|",
        ]

        for f in files:
            cov = f["coverage_percent"]
            cov_str = f"{cov:.1f}%" if cov is not None else "N/A"
            has_test_str = "yes" if f["has_test"] else "no"
            lines.append(
                f"| `{f['source']}` | {f['language']} | {has_test_str}"
                f" | {f['spec_freshness']} | {cov_str} | {f['recommendation']} |"
            )

        lines += ["", "## Symbols per File", ""]
        for f in files:
            syms = f["symbols"]
            sym_str = ", ".join(f"`{s}`" for s in syms) if syms else "*none*"
            lines.append(f"- **`{f['source']}`**: {sym_str}")

        return {"result": "\n".join(lines)}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# map_paths
# ---------------------------------------------------------------------------


@mcp.tool(annotations=_READ_ONLY)
def map_paths(source_path: str) -> dict[str, Any]:
    """
    Return the source, test file, and spec file paths for a given source file.

    source_path: repo-relative path to the source file
    (e.g. "services/api/srv/jobs/jobs.go").

    Returns the three related paths so the caller knows where tests and specs
    live.  Returns an error for unsupported file types (e.g. plain text files
    with no language adapter).
    """
    try:
        paths = core.paths_for(source_path)
        lines = [
            "## Path Mapping",
            "",
            f"- **Source:**    `{paths['source']}`",
            f"- **Test file:** `{paths['test_path']}`",
            f"- **Spec file:** `{paths['spec_path']}`",
        ]
        return {"result": "\n".join(lines)}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# get_spec
# ---------------------------------------------------------------------------


@mcp.tool(annotations=_READ_ONLY)
def get_spec(source_path: str) -> dict[str, Any]:
    """
    Retrieve the stored test spec for a source file, including its freshness.

    source_path: repo-relative path to the source file.

    Shows: spec status, generated_from, updated date, freshness
    (missing/fresh/stale relative to current source), symbols covered, and the
    full spec body.  Reports clearly if no spec exists yet.
    """
    try:
        freshness = core.spec_freshness(source_path)
        spec = specstore.read_spec(source_path)

        if spec is None:
            return {
                "result": (
                    f"## Spec: `{source_path}`\n\n"
                    "**No spec found.** Use `write_spec` to create one."
                )
            }

        sym_str = ", ".join(spec.symbols) if spec.symbols else "*none*"
        lines = [
            f"## Spec: `{source_path}`",
            "",
            f"- **Status:**         {spec.status}",
            f"- **Generated from:** {spec.generated_from}",
            f"- **Updated:**        {spec.updated}",
            f"- **Freshness:**      {freshness}",
            f"- **Symbols:**        {sym_str}",
            "",
            "## Spec Body",
            "",
            spec.body,
        ]
        return {"result": "\n".join(lines)}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# check_spec_freshness
# ---------------------------------------------------------------------------


@mcp.tool(annotations=_READ_ONLY)
def check_spec_freshness(source_path: str) -> dict[str, Any]:
    """
    Check whether the stored spec is up-to-date with the current source code.

    source_path: repo-relative path to the source file.

    Returns one of three states with an explanation:
    - "missing": no spec has been written yet — use write_spec to create one.
    - "fresh": the spec fingerprint matches the current code, no action needed.
    - "stale": the code has changed since the spec was written — regenerate and
      re-save the spec.
    """
    try:
        freshness = core.spec_freshness(source_path)
        explanations: dict[str, str] = {
            "missing": (
                f"**missing** — no spec exists for `{source_path}` yet.\n\n"
                "Use `write_spec` to create one."
            ),
            "fresh": (
                f"**fresh** — the spec for `{source_path}` is up-to-date.\n\n"
                "The fingerprint in the spec matches the current source code."
            ),
            "stale": (
                f"**stale** — the spec for `{source_path}` is out of date.\n\n"
                "The source code has changed since the spec was last written. "
                "Regenerate and re-save the spec using `write_spec`."
            ),
        }
        msg = explanations.get(freshness, freshness)
    except Exception as e:
        return {"error": str(e)}
    else:
        return {"result": f"## Spec Freshness: `{source_path}`\n\n{msg}"}


# ---------------------------------------------------------------------------
# write_spec
# ---------------------------------------------------------------------------


@mcp.tool()
def write_spec(
    source_path: str,
    body: str,
    symbols: list[str],
    generated_from: str = "scratch",
    status: str = "draft",
) -> dict[str, Any]:
    """
    Write (or overwrite) the test spec for a source file.

    source_path: repo-relative path to the source file.
    body: the Markdown spec body (everything after the frontmatter).
    symbols: list of symbol names covered by this spec.
    generated_from: how the spec was produced — "scratch", "tests", or "mixed".
    status: "draft" (default) or "approved".

    The spec body must contain a ### <name> section for each symbol with
    the required fields: Contract, Rules, Cases, and Test level.  Call
    spec_template() to get a skeleton or validate_spec() to pre-check your
    body before writing.

    The spec fingerprint is computed automatically from the current source code,
    so freshness checking works immediately after writing.  Returns an error if
    the source file is missing, the file type is unsupported, the
    generated_from / status values are invalid, or the body is missing
    required per-symbol structure.
    """
    _valid_generated_from = {"scratch", "tests", "mixed"}
    _valid_status = {"draft", "approved"}

    if generated_from not in _valid_generated_from:
        return {
            "error": (
                f"invalid generated_from {generated_from!r}: "
                f"must be one of {sorted(_valid_generated_from)}"
            )
        }
    if status not in _valid_status:
        return {
            "error": (
                f"invalid status {status!r}: "
                f"must be one of {sorted(_valid_status)}"
            )
        }

    try:
        spec_path = core.write_spec(source_path, body, symbols, generated_from, status)
        sym_str = ", ".join(symbols) if symbols else "*none*"
        lines = [
            "## Spec Written",
            "",
            f"- **Source:**         `{source_path}`",
            f"- **Spec path:**      `{spec_path}`",
            f"- **Status:**         {status}",
            f"- **Generated from:** {generated_from}",
            f"- **Symbols:**        {sym_str}",
        ]
        return {"result": "\n".join(lines)}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# spec_template
# ---------------------------------------------------------------------------


@mcp.tool(annotations=_READ_ONLY)
def spec_template(source_path: str) -> dict[str, Any]:
    """
    Return a fill-in-the-blanks spec skeleton for a source file (one block per
    symbol with the required fields). Fill it, then write_spec.

    source_path: repo-relative path to the source file.

    Returns a Markdown skeleton with one ### <name> block per symbol detected
    in the source, each containing placeholder entries for all required fields:
    Contract, Rules, Cases, and Test level.  Replace the _TODO_ markers with
    real content, then pass the filled body to write_spec.
    """
    try:
        result = core.spec_template(source_path)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# validate_spec
# ---------------------------------------------------------------------------


@mcp.tool(annotations=_READ_ONLY)
def validate_spec(source_path: str, body: str) -> dict[str, Any]:
    """
    Pre-check a spec body before write_spec.

    source_path: repo-relative path to the source file (used to derive symbols).
    body: the Markdown spec body to validate.

    Checks that the body contains a ### <name> section for every symbol in
    source_path, and that each section includes the required fields (Contract,
    Rules, Cases, Test level).  Returns a lint result — "result", not "error" —
    whether the body is valid or not, so the model can inspect and self-correct
    without triggering a hard failure.
    """
    try:
        problems = core.validate_spec(source_path, body)
    except Exception as e:
        return {"error": str(e)}

    if not problems:
        return {"result": "Spec is valid — all required per-symbol fields present."}
    return {"result": "Spec NOT valid yet:\n- " + "\n- ".join(problems)}


# ---------------------------------------------------------------------------
# list_reference_tests
# ---------------------------------------------------------------------------


@mcp.tool(annotations=_READ_ONLY)
def list_reference_tests(package: str) -> dict[str, Any]:
    """
    List golden/reference test files for a package to use as style guides.

    package: repo-relative path to the package directory
    (e.g. "services/api/srv/jobs").

    Returns paths of existing test files in the package directory plus any
    hard-coded golden examples the language adapter knows about.  Returns a
    note if none are found.
    """
    try:
        paths = core.reference_tests_for(package)
        if not paths:
            return {
                "result": (
                    f"## Reference Tests: `{package}`\n\n"
                    "*No reference test files found for this package.*"
                )
            }
        lines = [
            f"## Reference Tests: `{package}`",
            "",
            "The following test files can be used as style references:",
            "",
        ]
        lines.extend(f"- `{p}`" for p in paths)
        return {"result": "\n".join(lines)}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# resolve_test_command
# ---------------------------------------------------------------------------


@mcp.tool(annotations=_READ_ONLY)
def resolve_test_command(package: str) -> dict[str, Any]:
    """
    Show the test and coverage commands for a package.

    package: repo-relative path to the package directory
    (e.g. "services/api/srv/jobs").

    Returns both the unit-test command and the coverage command for the
    package's language.  These commands run on the build machine or in CI —
    they cannot be executed locally.
    """
    try:
        cmds = core.commands_for(package)
        lines = [
            f"## Test Commands: `{package}`",
            "",
            "**Test:**",
            "```",
            cmds["test"],
            "```",
            "",
            "**Coverage:**",
            "```",
            cmds["coverage"],
            "```",
            "",
            "> **Note:** These commands run on the build machine or in CI, not locally.",
        ]
        return {"result": "\n".join(lines)}
    except Exception as e:
        return {"error": str(e)}
