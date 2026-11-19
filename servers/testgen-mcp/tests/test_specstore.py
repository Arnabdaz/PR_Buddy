"""Tests for testgen_mcp_server.specstore."""

from __future__ import annotations

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# TestSpecRelPath
# ---------------------------------------------------------------------------


class TestSpecRelPath:
    def test_nested_go_path(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import spec_rel_path

        result = spec_rel_path("services/api/srv/runtimes/runtimes.go")
        assert result == "testspecs/services/api/srv/runtimes/runtimes.spec.md"

    def test_lands_under_testspecs(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import spec_rel_path

        result = spec_rel_path("foo/bar.py")
        assert result.startswith("testspecs/")

    def test_stem_drops_final_extension_only(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import spec_rel_path

        # "foo.go" -> "foo.spec.md" (not "foo.go.spec.md")
        result = spec_rel_path("pkg/foo.go")
        assert result == "testspecs/pkg/foo.spec.md"

    def test_root_level_source(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import spec_rel_path

        result = spec_rel_path("main.go")
        assert result == "testspecs/main.spec.md"


# ---------------------------------------------------------------------------
# TestFingerprint
# ---------------------------------------------------------------------------


class TestFingerprint:
    def test_determinism(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import fingerprint

        sources = {"FuncA": "def func_a(): pass", "FuncB": "def func_b(): return 1"}
        assert fingerprint(sources) == fingerprint(sources)

    def test_order_independence(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import fingerprint

        a = fingerprint({"FuncA": "body_a", "FuncB": "body_b"})
        b = fingerprint({"FuncB": "body_b", "FuncA": "body_a"})
        assert a == b

    def test_sensitivity(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import fingerprint

        base = fingerprint({"FuncA": "original body"})
        changed = fingerprint({"FuncA": "modified body"})
        assert base != changed

    def test_empty_dict_stability(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import fingerprint

        a = fingerprint({})
        b = fingerprint({})
        assert a == b
        assert a.startswith("sha256:")

    def test_prefix(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import fingerprint

        result = fingerprint({"fn": "body"})
        assert result.startswith("sha256:")


# ---------------------------------------------------------------------------
# TestWriteAndReadSpec
# ---------------------------------------------------------------------------


class TestWriteAndReadSpec:
    def test_round_trip_all_fields(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import read_spec, spec_rel_path, write_spec

        body = (
            "## Overview\n\n"
            "This spec describes the runtimes module.\n\n"
            "- item 1\n"
            "- item 2\n"
        )
        ret = write_spec(
            source_rel="services/api/srv/runtimes/runtimes.go",
            body=body,
            symbols=["ListRuntimes", "applyRuntimeFilter"],
            code_fingerprint="sha256:abcd1234",
            generated_from="scratch",
            status="draft",
            updated="2026-07-27",
        )

        # Returned path is repo-relative
        assert ret == "testspecs/services/api/srv/runtimes/runtimes.spec.md"

        # File exists at the expected location
        spec_file = repo_root / spec_rel_path("services/api/srv/runtimes/runtimes.go")
        assert spec_file.exists()

        # Round-trip: all fields survive
        spec = read_spec("services/api/srv/runtimes/runtimes.go")
        assert spec is not None
        assert spec.source == "services/api/srv/runtimes/runtimes.go"
        assert spec.symbols == ["ListRuntimes", "applyRuntimeFilter"]
        assert spec.code_fingerprint == "sha256:abcd1234"
        assert spec.generated_from == "scratch"
        assert spec.status == "draft"
        assert spec.updated == "2026-07-27"
        assert spec.body == body

    def test_multiline_body_with_triple_dash_line(self, repo_root: Path) -> None:
        """A bare '---' line in the body must NOT be misread as frontmatter end."""
        from testgen_mcp_server.specstore import read_spec, write_spec

        body = "First section.\n\n---\n\nSecond section.\n"
        write_spec(
            source_rel="pkg/foo.go",
            body=body,
            symbols=["Foo"],
            code_fingerprint="sha256:cafe",
            generated_from="tests",
            status="approved",
            updated="2026-01-01",
        )
        spec = read_spec("pkg/foo.go")
        assert spec is not None
        assert spec.body == body

    def test_symbols_list_preserved(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import read_spec, write_spec

        syms = ["Alpha", "Beta", "Gamma"]
        write_spec(
            source_rel="a/b.go",
            body="body\n",
            symbols=syms,
            code_fingerprint="sha256:0000",
            generated_from="scratch",
            status="draft",
            updated="2026-07-01",
        )
        spec = read_spec("a/b.go")
        assert spec is not None
        assert spec.symbols == syms

    def test_empty_symbols_list(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import read_spec, write_spec

        write_spec(
            source_rel="a/c.go",
            body="body\n",
            symbols=[],
            code_fingerprint="sha256:0000",
            generated_from="scratch",
            status="draft",
            updated="2026-07-01",
        )
        spec = read_spec("a/c.go")
        assert spec is not None
        assert spec.symbols == []


# ---------------------------------------------------------------------------
# TestReadSpecAbsent
# ---------------------------------------------------------------------------


class TestReadSpecAbsent:
    def test_returns_none_when_file_missing(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import read_spec

        assert read_spec("nonexistent/path.go") is None


# ---------------------------------------------------------------------------
# TestFreshness
# ---------------------------------------------------------------------------


class TestFreshness:
    def test_missing_when_no_file(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import freshness

        assert freshness("no/such/file.go", "sha256:anything") == "missing"

    def test_fresh_when_fingerprint_matches(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import freshness, write_spec

        fp = "sha256:matchme"
        write_spec(
            source_rel="src/x.go",
            body="body\n",
            symbols=["X"],
            code_fingerprint=fp,
            generated_from="scratch",
            status="draft",
            updated="2026-07-01",
        )
        assert freshness("src/x.go", fp) == "fresh"

    def test_stale_when_fingerprint_differs(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import freshness, write_spec

        write_spec(
            source_rel="src/y.go",
            body="body\n",
            symbols=["Y"],
            code_fingerprint="sha256:old",
            generated_from="scratch",
            status="draft",
            updated="2026-07-01",
        )
        assert freshness("src/y.go", "sha256:new") == "stale"


# ---------------------------------------------------------------------------
# TestWriteSpecUpdatedDate
# ---------------------------------------------------------------------------


class TestWriteSpecUpdatedDate:
    def test_none_updated_writes_valid_iso_date(self, repo_root: Path) -> None:
        from testgen_mcp_server.specstore import read_spec, write_spec

        write_spec(
            source_rel="date/check.go",
            body="body\n",
            symbols=[],
            code_fingerprint="sha256:0",
            generated_from="scratch",
            status="draft",
            updated=None,
        )
        spec = read_spec("date/check.go")
        assert spec is not None
        assert len(spec.updated) == 10
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", spec.updated) is not None


# ---------------------------------------------------------------------------
# TestSpecSchemaVersion
# ---------------------------------------------------------------------------


class TestSpecSchemaVersion:
    def test_spec_schema_version_round_trips(self, repo_root: Path) -> None:
        """spec_schema_version written to frontmatter is read back correctly."""
        from testgen_mcp_server.spec_schema import SPEC_SCHEMA_VERSION
        from testgen_mcp_server.specstore import read_spec, write_spec

        write_spec(
            source_rel="sv/check.go",
            body="body\n",
            symbols=[],
            code_fingerprint="sha256:0",
            generated_from="scratch",
            status="draft",
            updated="2026-07-01",
        )
        spec = read_spec("sv/check.go")
        assert spec is not None
        assert spec.spec_schema_version == SPEC_SCHEMA_VERSION

    def test_spec_schema_version_defaults_to_1_when_absent(self, repo_root: Path) -> None:
        """An older spec file that has no spec_schema_version line defaults to 1."""
        from testgen_mcp_server.config import get_config
        from testgen_mcp_server.specstore import read_spec, spec_rel_path

        # Write a legacy-style spec without the spec_schema_version field.
        rel = spec_rel_path("old/legacy.go")
        cfg = get_config()
        spec_path = cfg.repo_root / rel
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(
            "---\n"
            "source: old/legacy.go\n"
            "symbols: []\n"
            "code_fingerprint: sha256:old\n"
            "generated_from: scratch\n"
            "status: draft\n"
            "updated: 2025-01-01\n"
            "---\n"
            "legacy body\n",
            encoding="utf-8",
        )

        spec = read_spec("old/legacy.go")
        assert spec is not None
        assert spec.spec_schema_version == 1

    def test_spec_schema_version_custom_value_round_trips(self, repo_root: Path) -> None:
        """A custom spec_schema_version value is preserved through write→read."""
        from testgen_mcp_server.specstore import read_spec, write_spec

        write_spec(
            source_rel="sv2/check.go",
            body="body\n",
            symbols=[],
            code_fingerprint="sha256:x",
            generated_from="scratch",
            status="draft",
            updated="2026-07-01",
            spec_schema_version=99,
        )
        spec = read_spec("sv2/check.go")
        assert spec is not None
        assert spec.spec_schema_version == 99
