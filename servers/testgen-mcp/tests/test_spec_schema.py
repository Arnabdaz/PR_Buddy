"""Tests for testgen_mcp_server.spec_schema."""

from __future__ import annotations

from pathlib import Path

from testgen_mcp_server.spec_schema import (
    REQUIRED_FIELDS,
    is_valid,
    render_template,
    validate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_valid_body(symbols: list[str]) -> str:
    """Build a minimally-valid body with all required fields for each symbol."""
    lines: list[str] = []
    for sym in symbols:
        lines += [
            f"### {sym}",
            "- **Contract:** does something useful",
            "- **Rules:** 1. always succeeds",
            "- **Cases:** | 1 | input | output |",
            "- **Test level:** unit",
            "",
        ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# TestRenderTemplate
# ---------------------------------------------------------------------------


class TestRenderTemplate:
    def test_contains_block_per_symbol(self, repo_root: Path) -> None:
        body = render_template("pkg/foo.go", ["Foo", "Bar"])
        assert "### Foo" in body
        assert "### Bar" in body

    def test_required_field_labels_present_in_each_block(self, repo_root: Path) -> None:
        body = render_template("pkg/foo.go", ["MyFunc"])
        for field in REQUIRED_FIELDS:
            assert field in body, f"missing required field label: {field!r}"

    def test_contains_source_rel_in_header(self, repo_root: Path) -> None:
        body = render_template("services/api/srv/jobs/jobs.go", ["ListJobs"])
        assert "services/api/srv/jobs/jobs.go" in body

    def test_package_purpose_appears_when_provided(self, repo_root: Path) -> None:
        body = render_template("pkg/foo.go", [], package_purpose="Does X")
        assert "Does X" in body

    def test_todo_placeholder_when_no_purpose(self, repo_root: Path) -> None:
        body = render_template("pkg/foo.go", [])
        assert "_TODO" in body

    def test_symbols_header_present_even_with_empty_list(self, repo_root: Path) -> None:
        body = render_template("pkg/foo.go", [])
        assert "## Symbols" in body

    def test_no_symbol_block_for_empty_list(self, repo_root: Path) -> None:
        body = render_template("pkg/foo.go", [])
        assert "### " not in body

    def test_symbols_appear_in_given_order(self, repo_root: Path) -> None:
        body = render_template("pkg/foo.go", ["Alpha", "Beta", "Gamma"])
        idx_alpha = body.index("### Alpha")
        idx_beta = body.index("### Beta")
        idx_gamma = body.index("### Gamma")
        assert idx_alpha < idx_beta < idx_gamma

    def test_test_level_field_label_in_template(self, repo_root: Path) -> None:
        """The template uses 'Test level & fixtures' which contains 'Test level'."""
        body = render_template("pkg/foo.go", ["Fn"])
        assert "Test level" in body


# ---------------------------------------------------------------------------
# TestValidate
# ---------------------------------------------------------------------------


class TestValidate:
    def test_returns_empty_for_valid_body(self, repo_root: Path) -> None:
        body = _make_valid_body(["Foo", "Bar"])
        assert validate(body, ["Foo", "Bar"]) == []

    def test_returns_empty_for_empty_symbols(self, repo_root: Path) -> None:
        assert validate("any body content", []) == []

    def test_flags_missing_section(self, repo_root: Path) -> None:
        body = _make_valid_body(["Foo"])  # only Foo has a section
        problems = validate(body, ["Foo", "MissingBar"])
        assert any("MissingBar" in p and "no '### ' section" in p for p in problems)

    def test_does_not_flag_present_symbol(self, repo_root: Path) -> None:
        body = _make_valid_body(["Foo"])
        problems = validate(body, ["Foo"])
        assert problems == []

    def test_flags_missing_required_fields(self, repo_root: Path) -> None:
        # Only Contract present; Rules, Cases, Test level missing
        body = "### Foo\n- **Contract:** does something\n"
        problems = validate(body, ["Foo"])
        assert problems
        # Should mention the symbol
        assert "Foo" in problems[0]

    def test_lists_all_missing_fields_in_one_problem_entry(self, repo_root: Path) -> None:
        """All missing required fields are reported together in one problem string."""
        body = "### Foo\n- just some text with no required fields present\n"
        problems = validate(body, ["Foo"])
        assert len(problems) == 1
        for field in REQUIRED_FIELDS:
            assert field in problems[0], (
                f"expected missing field {field!r} mentioned in: {problems[0]!r}"
            )

    def test_tolerates_bare_label_format(self, repo_root: Path) -> None:
        """Bare 'Contract:' (no bold markers) is accepted."""
        body = (
            "### Foo\n"
            "Contract: one sentence\n"
            "Rules: 1. always\n"
            "Cases: | 1 | x | y |\n"
            "Test level: unit\n"
        )
        assert validate(body, ["Foo"]) == []

    def test_tolerates_bold_colon_format(self, repo_root: Path) -> None:
        """**Contract:** (bold with colon) is accepted."""
        body = (
            "### Foo\n"
            "**Contract:** one sentence\n"
            "**Rules:** 1. always\n"
            "**Cases:** | 1 | x | y |\n"
            "**Test level:** unit\n"
        )
        assert validate(body, ["Foo"]) == []

    def test_tolerates_bold_no_colon_format(self, repo_root: Path) -> None:
        """**Contract** (bold without colon) is accepted."""
        body = (
            "### Foo\n"
            "**Contract** one sentence\n"
            "**Rules** 1. always\n"
            "**Cases** | 1 | x | y |\n"
            "**Test level** unit\n"
        )
        assert validate(body, ["Foo"]) == []

    def test_tolerates_test_level_and_fixtures(self, repo_root: Path) -> None:
        """'Test level & fixtures:' satisfies the 'Test level' requirement."""
        body = (
            "### Foo\n"
            "- **Contract:** does something\n"
            "- **Rules:** 1. always\n"
            "- **Cases:** | 1 | x | y |\n"
            "- **Test level & fixtures:** unit; dbmocks\n"
        )
        assert validate(body, ["Foo"]) == []

    def test_matches_qualified_name_via_last_component(self, repo_root: Path) -> None:
        """mlapi.ListJobs is found under a '### ListJobs' heading."""
        body = _make_valid_body(["ListJobs"])  # heading is ### ListJobs
        assert validate(body, ["mlapi.ListJobs"]) == []

    def test_matches_fully_qualified_name_in_heading(self, repo_root: Path) -> None:
        """mlapi.ListJobs is found under a '### mlapi.ListJobs' heading."""
        body = _make_valid_body(["mlapi.ListJobs"])
        assert validate(body, ["mlapi.ListJobs"]) == []

    def test_unqualified_name_matches_qualified_heading(self, repo_root: Path) -> None:
        """'ListJobs' symbol is found under '### mlapi.ListJobs' heading."""
        body = _make_valid_body(["mlapi.ListJobs"])
        assert validate(body, ["ListJobs"]) == []

    def test_case_insensitive_field_matching(self, repo_root: Path) -> None:
        """Field labels are matched case-insensitively."""
        body = (
            "### Foo\n"
            "**contract:** one sentence\n"
            "**rules:** 1. always\n"
            "**cases:** | 1 | x | y |\n"
            "**test level:** unit\n"
        )
        assert validate(body, ["Foo"]) == []

    def test_multiple_symbols_multiple_problems(self, repo_root: Path) -> None:
        """One problem entry per symbol with missing section."""
        body = "# no sections here"
        problems = validate(body, ["Sym1", "Sym2", "Sym3"])
        assert len(problems) == 3


# ---------------------------------------------------------------------------
# TestIsValid
# ---------------------------------------------------------------------------


class TestIsValid:
    def test_true_for_valid_body(self, repo_root: Path) -> None:
        body = _make_valid_body(["Foo"])
        assert is_valid(body, ["Foo"]) is True

    def test_false_for_invalid_body(self, repo_root: Path) -> None:
        assert is_valid("### Foo\n- some content without required fields", ["Foo"]) is False

    def test_true_for_empty_symbols(self, repo_root: Path) -> None:
        assert is_valid("any body", []) is True
