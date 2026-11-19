"""Tests for testgen_mcp_server.engine.core."""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Sample source text fixtures
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

# Modified so HelloWorld body differs → fingerprint changes
_SAMPLE_GO_MODIFIED = """\
package pkg

func HelloWorld() string {
\treturn "hello world modified"
}

func Add(a, b int) int {
\treturn a + b
}
"""

_SAMPLE_TEST_GO = """\
package pkg

import "testing"

func TestHelloWorld(t *testing.T) {
\tif HelloWorld() != "hello" {
\t\tt.Fatal("unexpected result")
\t}
}
"""

# Coverprofile for pkg/sample.go: 2 statement blocks, 1 covered, 1 not
_SAMPLE_COVERPROFILE = """\
mode: set
github.infra.cloudera.com/Sense/cloudera-sense/pkg/sample.go:3.26,5.2 1 1
github.infra.cloudera.com/Sense/cloudera-sense/pkg/sample.go:7.24,9.2 1 0
"""


# ---------------------------------------------------------------------------
# TestReadSource
# ---------------------------------------------------------------------------


class TestReadSource:
    def test_returns_text_for_existing_file(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "sample.go").write_text(_SAMPLE_GO, encoding="utf-8")
        assert core.read_source("sample.go") == _SAMPLE_GO

    def test_returns_none_for_missing_file(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        assert not (repo_root / "does_not_exist.go").exists()
        assert core.read_source("does_not_exist.go") is None


# ---------------------------------------------------------------------------
# TestCurrentFingerprint
# ---------------------------------------------------------------------------


class TestCurrentFingerprint:
    def test_returns_sha256_prefix(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "fp.go").write_text(_SAMPLE_GO, encoding="utf-8")
        fp = core.current_fingerprint("fp.go")
        assert fp is not None
        assert fp.startswith("sha256:")

    def test_returns_none_for_missing_file(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        assert not (repo_root / "missing.go").exists()
        assert core.current_fingerprint("missing.go") is None

    def test_returns_none_for_unsupported_extension(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "file.txt").write_text("irrelevant", encoding="utf-8")
        assert core.current_fingerprint("file.txt") is None

    def test_changes_when_function_body_changes(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        p = repo_root / "changing.go"
        p.write_text(_SAMPLE_GO, encoding="utf-8")
        fp_before = core.current_fingerprint("changing.go")

        p.write_text(_SAMPLE_GO_MODIFIED, encoding="utf-8")
        fp_after = core.current_fingerprint("changing.go")

        assert fp_before is not None
        assert fp_after is not None
        assert fp_before != fp_after

    def test_stable_when_file_unchanged(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "stable.go").write_text(_SAMPLE_GO, encoding="utf-8")
        fp1 = core.current_fingerprint("stable.go")
        fp2 = core.current_fingerprint("stable.go")
        assert fp1 == fp2


# ---------------------------------------------------------------------------
# TestPathsFor
# ---------------------------------------------------------------------------


class TestPathsFor:
    def test_go_file_returns_correct_paths(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        assert repo_root.is_dir()  # fixture sets up the repo root env
        result = core.paths_for("services/api/srv/jobs/jobs.go")
        assert result["source"] == "services/api/srv/jobs/jobs.go"
        assert result["test_path"] == "services/api/srv/jobs/jobs_test.go"
        assert result["spec_path"] == "testspecs/services/api/srv/jobs/jobs.spec.md"

    def test_unsupported_extension_raises_value_error(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        assert repo_root.is_dir()
        with pytest.raises(ValueError, match="unsupported file type"):
            core.paths_for("foo/bar.txt")

    def test_unsupported_extension_message_includes_path(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        assert repo_root.is_dir()

        with pytest.raises(ValueError, match=r"my/path\.json"):
            core.paths_for("my/path.json")


# ---------------------------------------------------------------------------
# TestSpecFreshness
# ---------------------------------------------------------------------------


class TestSpecFreshness:
    def test_missing_when_no_spec_written(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "fresh_test.go").write_text(_SAMPLE_GO, encoding="utf-8")
        # note: this is a Go file not ending in _test.go in the name fixture
        (repo_root / "nosspec.go").write_text(_SAMPLE_GO, encoding="utf-8")
        assert core.spec_freshness("nosspec.go") == "missing"

    def test_fresh_immediately_after_write(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "freshtest.go").write_text(_SAMPLE_GO, encoding="utf-8")
        core.write_spec("freshtest.go", "body\n", [], "scratch", "draft")
        assert core.spec_freshness("freshtest.go") == "fresh"

    def test_stale_after_source_changes(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        p = repo_root / "staletest.go"
        p.write_text(_SAMPLE_GO, encoding="utf-8")
        core.write_spec("staletest.go", "body\n", [], "scratch", "draft")
        p.write_text(_SAMPLE_GO_MODIFIED, encoding="utf-8")
        assert core.spec_freshness("staletest.go") == "stale"


# ---------------------------------------------------------------------------
# TestDetectGaps — all four recommendation branches
# ---------------------------------------------------------------------------


class TestDetectGaps:
    def _write_go(self, repo_root: Path, rel: str, text: str = _SAMPLE_GO) -> None:
        p = repo_root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def test_write_spec_from_code_when_no_spec_no_test(self, repo_root: Path) -> None:
        """No spec, no test → write_spec_from_code."""
        from testgen_mcp_server.engine import core

        self._write_go(repo_root, "pkg/a.go")
        result = core.detect_gaps("pkg/a.go")
        assert result["files"][0]["recommendation"] == "write_spec_from_code"
        assert result["files"][0]["has_spec"] is False
        assert result["files"][0]["has_test"] is False

    def test_derive_spec_from_tests_when_no_spec_but_has_test(self, repo_root: Path) -> None:
        """No spec, has test → derive_spec_from_tests."""
        from testgen_mcp_server.engine import core

        self._write_go(repo_root, "pkg/b.go")
        self._write_go(repo_root, "pkg/b_test.go", _SAMPLE_TEST_GO)
        result = core.detect_gaps("pkg/b.go")
        assert result["files"][0]["recommendation"] == "derive_spec_from_tests"
        assert result["files"][0]["has_test"] is True

    def test_update_spec_when_spec_stale(self, repo_root: Path) -> None:
        """Stale spec → update_spec."""
        from testgen_mcp_server.engine import core

        p = repo_root / "pkg" / "c.go"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_SAMPLE_GO, encoding="utf-8")
        core.write_spec("pkg/c.go", "body\n", [], "scratch", "draft")
        p.write_text(_SAMPLE_GO_MODIFIED, encoding="utf-8")  # stale now
        result = core.detect_gaps("pkg/c.go")
        assert result["files"][0]["recommendation"] == "update_spec"

    def test_reuse_spec_when_spec_fresh(self, repo_root: Path) -> None:
        """Fresh spec → reuse_spec."""
        from testgen_mcp_server.engine import core

        self._write_go(repo_root, "pkg/d.go")
        core.write_spec("pkg/d.go", "body\n", [], "scratch", "draft")
        result = core.detect_gaps("pkg/d.go")
        assert result["files"][0]["recommendation"] == "reuse_spec"

    def test_directory_target_walks_source_files(self, repo_root: Path) -> None:
        """Directory target includes all non-test, non-generated source files."""
        from testgen_mcp_server.engine import core

        (repo_root / "mypkg").mkdir()
        (repo_root / "mypkg" / "a.go").write_text(_SAMPLE_GO, encoding="utf-8")
        (repo_root / "mypkg" / "b.go").write_text(_SAMPLE_GO, encoding="utf-8")
        (repo_root / "mypkg" / "b_test.go").write_text(_SAMPLE_TEST_GO, encoding="utf-8")
        (repo_root / "mypkg" / "readme.md").write_text("# docs", encoding="utf-8")

        result = core.detect_gaps("mypkg")
        sources = {f["source"] for f in result["files"]}

        assert "mypkg/a.go" in sources
        assert "mypkg/b.go" in sources
        # test and non-Go files excluded
        assert "mypkg/b_test.go" not in sources
        assert "mypkg/readme.md" not in sources

    def test_summary_counts_are_correct(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "smry").mkdir()
        (repo_root / "smry" / "x.go").write_text(_SAMPLE_GO, encoding="utf-8")
        (repo_root / "smry" / "y.go").write_text(_SAMPLE_GO, encoding="utf-8")

        result = core.detect_gaps("smry")
        s = result["summary"]
        assert s["total"] == 2
        assert s["missing_spec"] == 2
        assert s["stale_spec"] == 0
        assert s["no_test"] == 2

    def test_symbols_list_populated(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        self._write_go(repo_root, "pkg/sym.go")
        result = core.detect_gaps("pkg/sym.go")
        syms = result["files"][0]["symbols"]
        assert "HelloWorld" in syms
        assert "Add" in syms

    def test_invalid_target_raises(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        assert not (repo_root / "completely_nonexistent_dir_xyz").exists()
        with pytest.raises(ValueError, match="target not found"):
            core.detect_gaps("completely_nonexistent_dir_xyz")


# ---------------------------------------------------------------------------
# TestLoadCoverage
# ---------------------------------------------------------------------------


class TestLoadCoverage:
    def test_parses_coverprofile_into_dict(self, repo_root: Path) -> None:
        from testgen_mcp_server.config import get_config
        from testgen_mcp_server.engine import core

        cfg = get_config()
        cov_dir = repo_root / cfg.coverage_dir
        cov_dir.mkdir(parents=True, exist_ok=True)
        (cov_dir / "pkg.coverprofile").write_text(_SAMPLE_COVERPROFILE, encoding="utf-8")

        cov_map = core._load_coverage()
        assert "pkg/sample.go" in cov_map
        fc = cov_map["pkg/sample.go"]
        assert fc.total_stmts == 2
        assert fc.covered_stmts == 1

    def test_coverage_percent_calculated(self, repo_root: Path) -> None:
        from testgen_mcp_server.config import get_config
        from testgen_mcp_server.engine import core

        cfg = get_config()
        cov_dir = repo_root / cfg.coverage_dir
        cov_dir.mkdir(parents=True, exist_ok=True)
        (cov_dir / "pkg.coverprofile").write_text(_SAMPLE_COVERPROFILE, encoding="utf-8")

        cov_map = core._load_coverage()
        assert cov_map["pkg/sample.go"].percent == 50.0

    def test_detect_gaps_surfaces_coverage_percent(self, repo_root: Path) -> None:
        """detect_gaps picks up coverage_percent from the loaded coverprofile."""
        from testgen_mcp_server.config import get_config
        from testgen_mcp_server.engine import core

        cfg = get_config()
        cov_dir = repo_root / cfg.coverage_dir
        cov_dir.mkdir(parents=True, exist_ok=True)
        (cov_dir / "pkg.coverprofile").write_text(_SAMPLE_COVERPROFILE, encoding="utf-8")

        (repo_root / "pkg").mkdir(parents=True, exist_ok=True)
        (repo_root / "pkg" / "sample.go").write_text(_SAMPLE_GO, encoding="utf-8")

        result = core.detect_gaps("pkg/sample.go")
        assert result["files"], "expected at least one file record"
        cov = result["files"][0]["coverage_percent"]
        assert cov is not None
        assert 0.0 <= cov <= 100.0

    def test_returns_empty_when_coverage_dir_missing(self, repo_root: Path) -> None:
        from testgen_mcp_server.config import get_config
        from testgen_mcp_server.engine import core

        # confirm the coverage dir is truly absent before calling
        assert not (repo_root / get_config().coverage_dir).exists()
        result = core._load_coverage()
        assert result == {}

    def test_skips_unreadable_coverage_files(self, repo_root: Path) -> None:
        from testgen_mcp_server.config import get_config
        from testgen_mcp_server.engine import core

        cfg = get_config()
        cov_dir = repo_root / cfg.coverage_dir
        cov_dir.mkdir(parents=True, exist_ok=True)
        (cov_dir / "bad.coverprofile").write_text(
            "mode: set\nnot valid data\n", encoding="utf-8"
        )
        # Should not raise; bad lines silently skipped
        result = core._load_coverage()
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# TestWriteSpec
# ---------------------------------------------------------------------------


class TestWriteSpec:
    def test_returns_spec_rel_path(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "ws.go").write_text(_SAMPLE_GO, encoding="utf-8")
        path = core.write_spec("ws.go", "body\n", [], "scratch", "draft")
        assert path == "testspecs/ws.spec.md"

    def test_file_is_created_on_disk(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "ws2.go").write_text(_SAMPLE_GO, encoding="utf-8")
        core.write_spec("ws2.go", "body\n", [], "scratch", "draft")
        assert (repo_root / "testspecs" / "ws2.spec.md").exists()

    def test_raises_for_missing_source(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        assert not (repo_root / "nowhere.go").exists()
        with pytest.raises(ValueError, match="unsupported or missing file"):
            core.write_spec("nowhere.go", "body", [], "scratch", "draft")

    def test_raises_for_unsupported_type(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "file.txt").write_text("text", encoding="utf-8")
        with pytest.raises(ValueError, match="unsupported or missing"):
            core.write_spec("file.txt", "body", [], "scratch", "draft")


# ---------------------------------------------------------------------------
# TestCommandsFor / TestReferenceTestsFor
# ---------------------------------------------------------------------------


class TestCommandsFor:
    def test_returns_go_test_and_coverage_commands(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "mypkg").mkdir()
        (repo_root / "mypkg" / "main.go").write_text(_SAMPLE_GO, encoding="utf-8")
        cmds = core.commands_for("mypkg")
        assert "go test" in cmds["test"]
        assert "go test" in cmds["coverage"]
        assert "coverage" in cmds["coverage"]

    def test_package_path_included_in_command(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "services" / "api").mkdir(parents=True)
        (repo_root / "services" / "api" / "handler.go").write_text(
            _SAMPLE_GO, encoding="utf-8"
        )
        cmds = core.commands_for("services/api")
        assert "services/api" in cmds["test"]

    def test_fallback_to_go_adapter_for_empty_dir(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "emptypkg").mkdir()
        cmds = core.commands_for("emptypkg")
        assert "go test" in cmds["test"]


class TestReferenceTestsFor:
    def test_returns_list_type(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        assert repo_root.is_dir()  # fixture sets TESTGEN_REPO_ROOT
        result = core.reference_tests_for("services/api/srv/jobs")
        assert isinstance(result, list)

    def test_returns_test_files_from_package_dir(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "mypkg2").mkdir()
        (repo_root / "mypkg2" / "x_test.go").write_text(
            _SAMPLE_TEST_GO, encoding="utf-8"
        )
        result = core.reference_tests_for("mypkg2")
        assert any("x_test.go" in p for p in result)


# ---------------------------------------------------------------------------
# TestWriteSpecValidation
# ---------------------------------------------------------------------------


# A minimal body that satisfies validation for a single symbol "HelloWorld".
_VALID_BODY_HW = (
    "### HelloWorld\n"
    "- **Contract:** returns the greeting string\n"
    "- **Rules:** 1. always returns 'hello'\n"
    "- **Cases:** | 1 | none | 'hello' |\n"
    "- **Test level:** unit\n"
)

# A valid body covering both symbols in _SAMPLE_GO.
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


class TestWriteSpecValidation:
    def test_rejects_invalid_body(self, repo_root: Path) -> None:
        """write_spec raises ValueError for a body that has no ### sections."""
        from testgen_mcp_server.engine import core

        (repo_root / "val.go").write_text(_SAMPLE_GO, encoding="utf-8")
        with pytest.raises(ValueError, match="required structure"):
            core.write_spec("val.go", "bad body\n", ["HelloWorld"], "scratch", "draft")

    def test_accepts_valid_body(self, repo_root: Path) -> None:
        """write_spec succeeds for a structurally-valid body."""
        from testgen_mcp_server.engine import core

        (repo_root / "valid.go").write_text(_SAMPLE_GO, encoding="utf-8")
        path = core.write_spec("valid.go", _VALID_BODY_HW, ["HelloWorld"], "scratch", "draft")
        assert path == "testspecs/valid.spec.md"

    def test_error_message_mentions_fix_retry(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "err.go").write_text(_SAMPLE_GO, encoding="utf-8")
        with pytest.raises(ValueError) as exc_info:
            core.write_spec("err.go", "bad body", ["HelloWorld"], "scratch", "draft")
        assert "fix and retry" in str(exc_info.value)

    def test_error_message_mentions_helper_tools(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "err2.go").write_text(_SAMPLE_GO, encoding="utf-8")
        with pytest.raises(ValueError) as exc_info:
            core.write_spec("err2.go", "bad body", ["HelloWorld"], "scratch", "draft")
        msg = str(exc_info.value)
        assert "spec_template()" in msg
        assert "validate_spec()" in msg

    def test_empty_symbols_bypasses_validation(self, repo_root: Path) -> None:
        """Empty symbols list means no structure check — simple bodies are fine."""
        from testgen_mcp_server.engine import core

        (repo_root / "nosym.go").write_text(_SAMPLE_GO, encoding="utf-8")
        path = core.write_spec("nosym.go", "simple body\n", [], "scratch", "draft")
        assert path == "testspecs/nosym.spec.md"


# ---------------------------------------------------------------------------
# TestSpecTemplate
# ---------------------------------------------------------------------------


class TestSpecTemplate:
    def test_returns_skeleton_with_symbol_blocks(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "tmpl.go").write_text(_SAMPLE_GO, encoding="utf-8")
        skeleton = core.spec_template("tmpl.go")
        assert "### HelloWorld" in skeleton
        assert "### Add" in skeleton

    def test_returns_required_field_labels(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core
        from testgen_mcp_server.spec_schema import REQUIRED_FIELDS

        (repo_root / "tmpl2.go").write_text(_SAMPLE_GO, encoding="utf-8")
        skeleton = core.spec_template("tmpl2.go")
        for field in REQUIRED_FIELDS:
            assert field in skeleton, f"missing required field label: {field!r}"

    def test_raises_for_missing_source(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        assert not (repo_root / "nonexistent.go").exists()
        with pytest.raises(ValueError):
            core.spec_template("nonexistent.go")

    def test_raises_for_unsupported_type(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "file.txt").write_text("text", encoding="utf-8")
        with pytest.raises(ValueError):
            core.spec_template("file.txt")

    def test_uses_provided_symbols_override(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "tmpl3.go").write_text(_SAMPLE_GO, encoding="utf-8")
        skeleton = core.spec_template("tmpl3.go", symbols=["MyCustomFunc"])
        assert "### MyCustomFunc" in skeleton
        assert "### HelloWorld" not in skeleton

    def test_skeleton_passes_validation(self, repo_root: Path) -> None:
        """The rendered skeleton should NOT pass validation (has _TODO_ placeholders),
        but the required field *labels* must all be present so the model can fill them in."""
        from testgen_mcp_server.engine import core
        from testgen_mcp_server.spec_schema import REQUIRED_FIELDS

        (repo_root / "tmpl4.go").write_text(_SAMPLE_GO, encoding="utf-8")
        skeleton = core.spec_template("tmpl4.go")
        # All required field labels are present in the skeleton
        for field in REQUIRED_FIELDS:
            assert field in skeleton


# ---------------------------------------------------------------------------
# TestValidateSpec
# ---------------------------------------------------------------------------


class TestValidateSpec:
    def test_returns_problems_for_missing_sections(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "vs.go").write_text(_SAMPLE_GO, encoding="utf-8")
        problems = core.validate_spec("vs.go", "bad body with no sections")
        assert len(problems) > 0
        assert any("HelloWorld" in p for p in problems)
        assert any("Add" in p for p in problems)

    def test_returns_empty_for_valid_body(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "vs2.go").write_text(_SAMPLE_GO, encoding="utf-8")
        problems = core.validate_spec("vs2.go", _VALID_BODY_BOTH)
        assert problems == []

    def test_uses_provided_symbols_override(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "vs3.go").write_text(_SAMPLE_GO, encoding="utf-8")
        # Override with empty list → no checks
        problems = core.validate_spec("vs3.go", "some body", symbols=[])
        assert problems == []

    def test_raises_for_unsupported_type(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        (repo_root / "vs4.txt").write_text("text", encoding="utf-8")
        with pytest.raises(ValueError, match="unsupported"):
            core.validate_spec("vs4.txt", "body")

    def test_raises_for_missing_source(self, repo_root: Path) -> None:
        from testgen_mcp_server.engine import core

        assert not (repo_root / "missing_vs.go").exists()
        with pytest.raises(ValueError):
            core.validate_spec("missing_vs.go", "body")
