"""Shared pytest fixtures for testgen-mcp tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from testgen_mcp_server.config import reset_config


@pytest.fixture()
def repo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Set up a temporary repo root for each test.

    Sets ``TESTGEN_REPO_ROOT`` to a fresh ``tmp_path``, sets
    ``TESTGEN_SPEC_DIR`` to ``"testspecs"``, and resets the config singleton
    before *and* after the test so each test sees a clean state.

    Returns the repo root ``Path`` so tests can create source files under it.
    """
    reset_config()
    monkeypatch.setenv("TESTGEN_REPO_ROOT", str(tmp_path))
    monkeypatch.setenv("TESTGEN_SPEC_DIR", "testspecs")
    yield tmp_path
    reset_config()
