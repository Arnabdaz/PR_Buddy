"""Tests for testgen_mcp_server.tools — MCP tool wrappers."""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Sample source text
# ---------------------------------------------------------------------------

_SAMPLE_GO = """\
package pkg

func HelloWorld() string {
\treturn "hello"
}

func Add(a, b int) int {
\treturn a + b
}
"""

_SAMPLE_GO_MODIFIED = """\
package pkg

func HelloWorld() string {
\treturn "hello world modified"
}

func Add(a, b int) int {
\treturn a + b + 1
}
"""


# ---------------------------------------------------------------------------
# TestDetectGapsTool
# ---------------------------------------------------------------------------


class TestDetectGapsTool:
    def test_returns_result_key_with_source_name(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import detect_gaps

        (repo_root / "t.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = detect_gaps("t.go")
        assert "result" in out
        assert "t.go" in out["result"]

    def test_shows_write_spec_from_code_recommendation(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import detect_gaps

        (repo_root / "t2.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = detect_gaps("t2.go")
        assert "write_spec_from_code" in out["result"]

    def test_shows_summary_counts(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import detect_gaps

        (repo_root / "t3.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = detect_gaps("t3.go")
        assert "Total files" in out["result"] or "total" in out["result"].lower()

    def test_error_on_nonexistent_target(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import detect_gaps

        assert not (repo_root / "totally_nonexistent_xyz_target").exists()
        out = detect_gaps("totally_nonexistent_xyz_target")
        assert "error" in out

    def test_shows_symbols_in_result(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import detect_gaps

        (repo_root / "sym.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = detect_gaps("sym.go")
        assert "HelloWorld" in out["result"]


# ---------------------------------------------------------------------------
# TestMapPathsTool
# ---------------------------------------------------------------------------


class TestMapPathsTool:
    def test_returns_source_test_spec_paths(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import map_paths

        assert repo_root.is_dir()  # fixture sets TESTGEN_REPO_ROOT
        out = map_paths("services/api/srv/jobs/jobs.go")
        assert "result" in out
        assert "jobs.go" in out["result"]
        assert "jobs_test.go" in out["result"]
        assert "jobs.spec.md" in out["result"]

    def test_error_for_unsupported_extension(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import map_paths

        assert repo_root.is_dir()
        out = map_paths("foo/bar.unsupported_extension_xyz")
        assert "error" in out


# ---------------------------------------------------------------------------
# TestWriteSpecTool + TestGetSpecTool (round-trip)
# ---------------------------------------------------------------------------


class TestWriteAndGetSpec:
    def test_write_then_get_round_trip(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import get_spec, write_spec

        (repo_root / "wg.go").write_text(_SAMPLE_GO, encoding="utf-8")

        # Use empty symbols so validation is bypassed (focus: round-trip I/O).
        wr = write_spec(
            source_path="wg.go",
            body="## Overview\nThis is a test spec.\n",
            symbols=[],
            generated_from="scratch",
            status="draft",
        )
        assert "result" in wr, f"unexpected: {wr}"
        assert "wg.go" in wr["result"]
        assert "draft" in wr["result"]

        gr = get_spec("wg.go")
        assert "result" in gr, f"unexpected: {gr}"
        assert "draft" in gr["result"]
        assert "Overview" in gr["result"]
        assert "fresh" in gr["result"]

    def test_get_spec_missing_returns_result_not_error(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import get_spec

        assert not (repo_root / "no_such_file.go").exists()
        out = get_spec("no_such_file.go")
        assert "result" in out
        assert "No spec found" in out["result"]

    def test_write_spec_rejects_invalid_generated_from(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import write_spec

        (repo_root / "bad_gf.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = write_spec(
            source_path="bad_gf.go",
            body="body",
            symbols=[],
            generated_from="ai_model",  # invalid
            status="draft",
        )
        assert "error" in out
        assert "generated_from" in out["error"]

    def test_write_spec_rejects_invalid_status(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import write_spec

        (repo_root / "bad_st.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = write_spec(
            source_path="bad_st.go",
            body="body",
            symbols=[],
            generated_from="scratch",
            status="published",  # invalid
        )
        assert "error" in out
        assert "status" in out["error"]

    def test_write_spec_error_for_missing_source(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import write_spec

        assert not (repo_root / "nonexistent_source.go").exists()
        out = write_spec(
            source_path="nonexistent_source.go",
            body="body",
            symbols=[],
            generated_from="scratch",
            status="draft",
        )
        assert "error" in out

    def test_write_approved_spec(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import get_spec, write_spec

        (repo_root / "approved.go").write_text(_SAMPLE_GO, encoding="utf-8")
        # Use empty symbols so validation is bypassed (focus: status round-trip).
        wr = write_spec(
            source_path="approved.go",
            body="approved spec body\n",
            symbols=[],
            generated_from="tests",
            status="approved",
        )
        assert "result" in wr
        assert "approved" in wr["result"]

        gr = get_spec("approved.go")
        assert "approved" in gr["result"]


# ---------------------------------------------------------------------------
# TestCheckFreshnessTool
# ---------------------------------------------------------------------------


class TestCheckFreshnessTool:
    def test_missing_when_no_spec(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import check_spec_freshness

        (repo_root / "cf.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = check_spec_freshness("cf.go")
        assert "result" in out
        assert "missing" in out["result"]

    def test_fresh_after_write(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import check_spec_freshness, write_spec

        (repo_root / "cf2.go").write_text(_SAMPLE_GO, encoding="utf-8")
        write_spec(
            source_path="cf2.go",
            body="body",
            symbols=[],
            generated_from="scratch",
            status="draft",
        )
        out = check_spec_freshness("cf2.go")
        assert "fresh" in out["result"]

    def test_stale_after_source_changes(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import check_spec_freshness, write_spec

        p = repo_root / "cf3.go"
        p.write_text(_SAMPLE_GO, encoding="utf-8")
        write_spec(
            source_path="cf3.go",
            body="body",
            symbols=[],
            generated_from="scratch",
            status="draft",
        )
        p.write_text(_SAMPLE_GO_MODIFIED, encoding="utf-8")
        out = check_spec_freshness("cf3.go")
        assert "stale" in out["result"]


# ---------------------------------------------------------------------------
# TestResolveTestCommandTool
# ---------------------------------------------------------------------------


class TestResolveTestCommandTool:
    def test_shows_go_test_command(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import resolve_test_command

        (repo_root / "mypkg3").mkdir()
        (repo_root / "mypkg3" / "main.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = resolve_test_command("mypkg3")
        assert "result" in out
        assert "go test" in out["result"]

    def test_includes_build_machine_note(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import resolve_test_command

        (repo_root / "mypkg4").mkdir()
        (repo_root / "mypkg4" / "main.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = resolve_test_command("mypkg4")
        result_lower = out["result"].lower()
        assert "build machine" in result_lower or "ci" in result_lower

    def test_shows_coverage_command(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import resolve_test_command

        (repo_root / "mypkg5").mkdir()
        (repo_root / "mypkg5" / "main.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = resolve_test_command("mypkg5")
        assert "coverage" in out["result"].lower() or "coverprofile" in out["result"]


# ---------------------------------------------------------------------------
# TestListReferenceTestsTool
# ---------------------------------------------------------------------------


class TestListReferenceTestsTool:
    def test_returns_result_key(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import list_reference_tests

        assert repo_root.is_dir()  # fixture sets TESTGEN_REPO_ROOT
        out = list_reference_tests("services/api/srv/jobs")
        assert "result" in out

    def test_includes_package_test_file_if_present(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import list_reference_tests

        (repo_root / "mypkg6").mkdir()
        (repo_root / "mypkg6" / "x_test.go").write_text(
            "package mypkg6\n", encoding="utf-8"
        )
        out = list_reference_tests("mypkg6")
        assert "x_test.go" in out["result"]

    def test_note_when_no_tests_found(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import list_reference_tests

        (repo_root / "emptypkg2").mkdir()
        out = list_reference_tests("emptypkg2")
        assert "result" in out
        assert "No reference test files found" in out["result"]


# ---------------------------------------------------------------------------
# Shared valid bodies for tools tests
# ---------------------------------------------------------------------------

_VALID_BODY_HW = (
    "### HelloWorld\n"
    "- **Contract:** returns the greeting string\n"
    "- **Rules:** 1. always returns 'hello'\n"
    "- **Cases:** | 1 | none | 'hello' |\n"
    "- **Test level:** unit\n"
)

_VALID_BODY_BOTH = (
    "### HelloWorld\n"
    "- **Contract:** returns the greeting string\n"
    "- **Rules:** 1. always returns 'hello'\n"
    "- **Cases:** | 1 | none | 'hello' |\n"
    "- **Test level:** unit\n"
    "\n"
    "### Add\n"
    "- **Contract:** returns the sum of two integers\n"
    "- **Rules:** 1. returns a + b\n"
    "- **Cases:** | 1 | a=1, b=2 | 3 |\n"
    "- **Test level:** unit\n"
)


# ---------------------------------------------------------------------------
# TestWriteSpecWithValidation
# ---------------------------------------------------------------------------


class TestWriteSpecWithValidation:
    def test_returns_error_for_invalid_body(self, repo_root: Path) -> None:
        """write_spec tool returns error when body is structurally invalid."""
        from testgen_mcp_server.tools import write_spec

        (repo_root / "inv.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = write_spec(
            source_path="inv.go",
            body="bad body with no sections",
            symbols=["HelloWorld"],
            generated_from="scratch",
            status="draft",
        )
        assert "error" in out
        assert "required structure" in out["error"]

    def test_error_message_guides_correction(self, repo_root: Path) -> None:
        """The error message includes the 'fix and retry' guidance."""
        from testgen_mcp_server.tools import write_spec

        (repo_root / "struct.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = write_spec(
            source_path="struct.go",
            body="bad body",
            symbols=["HelloWorld"],
            generated_from="scratch",
            status="draft",
        )
        assert "error" in out
        assert "fix and retry" in out["error"]

    def test_returns_result_for_valid_body(self, repo_root: Path) -> None:
        """write_spec tool succeeds when body has all required structure."""
        from testgen_mcp_server.tools import write_spec

        (repo_root / "good.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = write_spec(
            source_path="good.go",
            body=_VALID_BODY_HW,
            symbols=["HelloWorld"],
            generated_from="scratch",
            status="draft",
        )
        assert "result" in out

    def test_accepts_mixed_generated_from(self, repo_root: Path) -> None:
        """generated_from='mixed' is a valid value."""
        from testgen_mcp_server.tools import write_spec

        (repo_root / "mixed.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = write_spec(
            source_path="mixed.go",
            body="body with empty symbols list",
            symbols=[],
            generated_from="mixed",
            status="draft",
        )
        assert "result" in out

    def test_rejects_unknown_generated_from(self, repo_root: Path) -> None:
        """generated_from='ai_model' is still rejected."""
        from testgen_mcp_server.tools import write_spec

        (repo_root / "bge.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = write_spec(
            source_path="bge.go",
            body="body",
            symbols=[],
            generated_from="ai_model",
            status="draft",
        )
        assert "error" in out
        assert "generated_from" in out["error"]


# ---------------------------------------------------------------------------
# TestSpecTemplateTool
# ---------------------------------------------------------------------------


class TestSpecTemplateTool:
    def test_returns_result_with_field_labels(self, repo_root: Path) -> None:
        """spec_template tool returns a body containing all required field labels."""
        from testgen_mcp_server.spec_schema import REQUIRED_FIELDS
        from testgen_mcp_server.tools import spec_template

        (repo_root / "st.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = spec_template("st.go")
        assert "result" in out
        for field in REQUIRED_FIELDS:
            assert field in out["result"], f"missing required field label: {field!r}"

    def test_contains_symbol_blocks(self, repo_root: Path) -> None:
        """spec_template tool includes a ### block for each detected symbol."""
        from testgen_mcp_server.tools import spec_template

        (repo_root / "st2.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = spec_template("st2.go")
        assert "### HelloWorld" in out["result"]
        assert "### Add" in out["result"]

    def test_error_for_missing_source(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import spec_template

        out = spec_template("nonexistent.go")
        assert "error" in out

    def test_error_for_unsupported_type(self, repo_root: Path) -> None:
        from testgen_mcp_server.tools import spec_template

        (repo_root / "unsup.txt").write_text("text", encoding="utf-8")
        out = spec_template("unsup.txt")
        assert "error" in out


# ---------------------------------------------------------------------------
# TestValidateSpecTool
# ---------------------------------------------------------------------------


class TestValidateSpecTool:
    def test_valid_result_for_valid_body(self, repo_root: Path) -> None:
        """validate_spec returns a 'valid' result for a structurally-correct body."""
        from testgen_mcp_server.tools import validate_spec

        (repo_root / "vst.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = validate_spec("vst.go", _VALID_BODY_BOTH)
        assert "result" in out
        assert "valid" in out["result"].lower()
        assert "error" not in out

    def test_not_valid_result_for_invalid_body(self, repo_root: Path) -> None:
        """validate_spec returns a 'NOT valid' result for a body missing sections."""
        from testgen_mcp_server.tools import validate_spec

        (repo_root / "vst2.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = validate_spec("vst2.go", "bad body")
        assert "result" in out
        assert "NOT valid" in out["result"]

    def test_uses_result_not_error_for_lint_failure(self, repo_root: Path) -> None:
        """validate_spec always returns 'result', never 'error', for lint failures."""
        from testgen_mcp_server.tools import validate_spec

        (repo_root / "vst3.go").write_text(_SAMPLE_GO, encoding="utf-8")
        out = validate_spec("vst3.go", "bad body with no sections")
        assert "error" not in out
        assert "result" in out

    def test_error_for_missing_source(self, repo_root: Path) -> None:
        """validate_spec returns error when the source file does not exist."""
        from testgen_mcp_server.tools import validate_spec

        out = validate_spec("no_such_file.go", "some body")
        assert "error" in out

    def test_error_for_unsupported_type(self, repo_root: Path) -> None:
        """validate_spec returns error for unsupported file types."""
        from testgen_mcp_server.tools import validate_spec

        (repo_root / "unsup2.txt").write_text("text", encoding="utf-8")
        out = validate_spec("unsup2.txt", "some body")
        assert "error" in out
