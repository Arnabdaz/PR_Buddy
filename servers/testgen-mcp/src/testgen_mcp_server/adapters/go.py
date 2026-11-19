"""Go language adapter for the testgen MCP server."""

from __future__ import annotations

import re
from pathlib import Path

from .base import FileCoverage, Symbol

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Regex for top-level (column 0) Go function/method declarations.
# Matches: func (<recv>) <name>[<type-params>](
_FUNC_RE = re.compile(
    r"^func\s+(?:\((?P<recv>[^)]*)\)\s*)?(?P<name>[A-Za-z_]\w*)"
    r"\s*(?:\[[^\]]*\])?\s*\(",
    re.MULTILINE,
)

# Generated-code header: a line containing both markers (order: Code generated ... DO NOT EDIT).
# No re.DOTALL so '.' does not cross line boundaries — both tokens must be on the same line.
_GENERATED_RE = re.compile(r"Code generated.*DO NOT EDIT")

# Known generated directory prefixes (repo-relative POSIX paths).
_GENERATED_PATH_PREFIXES: tuple[str, ...] = (
    "services/api/srv/db/dbops/",
    "services/api/srv/db/models/",
)

# Golden example test files used as style references.
_GOLDEN_TESTS: tuple[str, ...] = (
    "services/api/srv/jobs/jobs_test.go",
    "services/api/srv/runtimes/runtimes_test.go",
    "services/api/srv/projects/projects_test.go",
)


# ---------------------------------------------------------------------------
# Go-aware text scanner helpers
# ---------------------------------------------------------------------------


def _find_body_open(text: str, pos: int) -> int:
    """Scan forward from pos (at the opening '(' of the param list) to the
    function body's opening '{', skipping comments and string/rune literals.

    Tracks paren depth so that '{' inside return-type parens is not mistaken
    for the body opener.  Returns -1 if not found.
    """
    n = len(text)
    paren_depth = 0
    i = pos
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            # Line comment — skip to end of line (leave '\n' for outer loop)
            while i < n and text[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            # Block comment — skip to */
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2  # consume */
        elif c == '"':
            # Interpreted string literal
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\":
                    i += 1  # skip escaped character
                i += 1
            i += 1  # consume closing "
        elif c == "`":
            # Raw string literal (no escape sequences)
            i += 1
            while i < n and text[i] != "`":
                i += 1
            i += 1  # consume closing `
        elif c == "'":
            # Rune literal
            i += 1
            while i < n and text[i] != "'":
                if text[i] == "\\":
                    i += 1  # skip escaped character
                i += 1
            i += 1  # consume closing '
        elif c == "(":
            paren_depth += 1
            i += 1
        elif c == ")":
            paren_depth -= 1
            i += 1
        elif c == "{" and paren_depth == 0:
            return i
        else:
            i += 1
    return -1


def _find_brace_close(text: str, open_brace: int) -> int:
    """Find the '}' matching the '{' at open_brace.

    Go-aware: braces inside line comments, block comments, interpreted strings,
    raw strings, and rune literals are ignored.  Returns -1 if unmatched.
    """
    n = len(text)
    depth = 1
    i = open_brace + 1
    while i < n and depth > 0:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
        elif c == '"':
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\":
                    i += 1
                i += 1
            i += 1
        elif c == "`":
            i += 1
            while i < n and text[i] != "`":
                i += 1
            i += 1
        elif c == "'":
            i += 1
            while i < n and text[i] != "'":
                if text[i] == "\\":
                    i += 1
                i += 1
            i += 1
        elif c == "{":
            depth += 1
            i += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
            i += 1
        else:
            i += 1
    return -1


def _pos_to_line(text: str, pos: int) -> int:
    """Convert a byte offset to a 1-based line number."""
    return text[:pos].count("\n") + 1


# ---------------------------------------------------------------------------
# GoAdapter
# ---------------------------------------------------------------------------


class GoAdapter:
    """Language adapter for Go source files.

    Implements the LanguageAdapter Protocol (structural subtype — no explicit
    inheritance needed).  All methods are pure/deterministic; the only state is
    the module_path used to strip coverage prefixes.
    """

    name: str = "go"

    def __init__(
        self,
        module_path: str = "github.infra.cloudera.com/Sense/cloudera-sense",
    ) -> None:
        self.module_path = module_path

    # ------------------------------------------------------------------
    # File-level predicates
    # ------------------------------------------------------------------

    def handles(self, source_rel: str) -> bool:
        """True iff the path ends with '.go'."""
        return source_rel.endswith(".go")

    def is_test_file(self, source_rel: str) -> bool:
        """True iff the path ends with '_test.go'."""
        return source_rel.endswith("_test.go")

    def is_generated(self, source_rel: str, source_text: str) -> bool:
        """True if the file is generated / must-not-edit.

        Conditions (any one sufficient):
        - source_text contains a line with both "Code generated" and "DO NOT EDIT"
        - path is under a known generated directory prefix
        - any path segment is exactly "mock"
        """
        if _GENERATED_RE.search(source_text):
            return True
        normalized = source_rel.replace("\\", "/")
        for prefix in _GENERATED_PATH_PREFIXES:
            if normalized.startswith(prefix):
                return True
        if "mock" in normalized.split("/"):
            return True
        return False

    # ------------------------------------------------------------------
    # Symbol extraction
    # ------------------------------------------------------------------

    def _iter_symbols(self, source_text: str) -> list[tuple[Symbol, int, int]]:
        """Return (Symbol, func_line_start_pos, close_brace_pos) for each
        top-level function/method declaration found in source_text."""
        results: list[tuple[Symbol, int, int]] = []
        for m in _FUNC_RE.finditer(source_text):
            recv_raw: str | None = m.group("recv")
            func_name: str = m.group("name")

            # m.end() is right after the '(' that opens the parameter list;
            # start scanning at that '(' so paren-depth tracking is correct.
            open_brace = _find_body_open(source_text, m.end() - 1)
            if open_brace < 0:
                continue
            close_brace = _find_brace_close(source_text, open_brace)
            if close_brace < 0:
                continue

            # Build qualified symbol name
            if recv_raw is not None:
                recv_parts = recv_raw.split()
                recv_type = recv_parts[-1].lstrip("*") if recv_parts else recv_raw
                sym_name = f"{recv_type}.{func_name}"
                kind = "method"
            else:
                sym_name = func_name
                kind = "func"

            start_line = _pos_to_line(source_text, m.start())
            end_line = _pos_to_line(source_text, close_brace)

            sym = Symbol(
                name=sym_name,
                kind=kind,
                receiver=recv_raw,
                start_line=start_line,
                end_line=end_line,
            )
            # Character position of the start of the line that holds 'func'
            line_start = source_text.rfind("\n", 0, m.start()) + 1
            results.append((sym, line_start, close_brace))
        return results

    def list_symbols(self, source_text: str) -> list[Symbol]:
        """Return all top-level Go func/method declarations."""
        return [sym for sym, _, _ in self._iter_symbols(source_text)]

    def extract_symbol_sources(self, source_text: str) -> dict[str, str]:
        """Map each symbol name to its exact source text (func line … closing }).

        Uses line numbers (already computed by _iter_symbols) to slice the
        source — this guarantees the extracted substring is self-contained and
        identical to what appears in the file.
        """
        lines = source_text.splitlines(keepends=True)
        result: dict[str, str] = {}
        for sym, _line_start, _close_pos in self._iter_symbols(source_text):
            result[sym.name] = "".join(lines[sym.start_line - 1 : sym.end_line])
        return result

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    def test_path(self, source_rel: str) -> str:
        """Return the conventional test file path for a source file.

        ``foo.go`` → ``foo_test.go``.  Already-test files are returned as-is.
        """
        if source_rel.endswith("_test.go"):
            return source_rel
        return source_rel[: -len(".go")] + "_test.go"

    # ------------------------------------------------------------------
    # Command helpers
    # ------------------------------------------------------------------

    def test_command(self, package_rel: str) -> str:
        """``go test ./<pkg>/...`` for the given package directory."""
        pkg = package_rel.strip("/")
        return f"go test ./{pkg}/..."

    def coverage_command(self, package_rel: str) -> str:
        """Run tests with coverprofile and print per-function coverage."""
        pkg = package_rel.strip("/")
        return (
            f"go test -coverprofile=coverage.out ./{pkg}/..."
            " && go tool cover -func=coverage.out"
        )

    # ------------------------------------------------------------------
    # Coverage parsing
    # ------------------------------------------------------------------

    def parse_coverage(self, raw: str) -> list[FileCoverage]:
        """Parse a Go coverprofile into per-file FileCoverage objects.

        Format (after the mode line):
            <import-path>:<startLine>.<startCol>,<endLine>.<endCol> <stmts> <count>

        The module_path prefix is stripped from import paths to give repo-relative
        source_rel values.  Malformed lines are silently skipped.
        """
        files: dict[str, FileCoverage] = {}
        prefix = self.module_path + "/"

        for raw_line in raw.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("mode:"):
                continue
            try:
                parts = line.split()
                if len(parts) != 3:  # noqa: PLR2004 (magic value acceptable here)
                    continue
                name_range, num_stmts_str, count_str = parts
                num_stmts = int(num_stmts_str)
                count = int(count_str)

                # Split at the LAST ':' to handle paths that might contain ':'
                colon_idx = name_range.rfind(":")
                if colon_idx < 0:
                    continue
                import_path = name_range[:colon_idx]
                range_str = name_range[colon_idx + 1 :]

                # Parse "startLine.startCol,endLine.endCol"
                comma_idx = range_str.index(",")
                start_line = int(range_str[:comma_idx].split(".")[0])
                end_line = int(range_str[comma_idx + 1 :].split(".")[0])

                # Strip module prefix to get repo-relative path
                source_rel = (
                    import_path[len(prefix) :]
                    if import_path.startswith(prefix)
                    else import_path
                )

                if source_rel not in files:
                    files[source_rel] = FileCoverage(
                        source_rel=source_rel,
                        covered_stmts=0,
                        total_stmts=0,
                    )
                fc = files[source_rel]
                fc.total_stmts += num_stmts
                if count > 0:
                    fc.covered_stmts += num_stmts
                    fc.covered_lines.update(range(start_line, end_line + 1))
                else:
                    fc.uncovered_lines.update(range(start_line, end_line + 1))

            except (ValueError, IndexError):
                continue  # skip malformed lines

        return list(files.values())

    # ------------------------------------------------------------------
    # Reference tests
    # ------------------------------------------------------------------

    def reference_tests(self, repo_root: str, package_rel: str) -> list[str]:
        """Return repo-relative paths of golden test files for style reference.

        Checks the hard-coded golden examples first, then any *_test.go files
        already present in the target package directory.  De-duplicated.
        """
        root = Path(repo_root)
        seen: set[str] = set()
        results: list[str] = []

        for candidate in _GOLDEN_TESTS:
            if (root / candidate).exists() and candidate not in seen:
                seen.add(candidate)
                results.append(candidate)

        pkg_dir = root / package_rel.strip("/")
        if pkg_dir.is_dir():
            for p in sorted(pkg_dir.glob("*_test.go")):
                rel = p.relative_to(root).as_posix()
                if rel not in seen:
                    seen.add(rel)
                    results.append(rel)

        return results
