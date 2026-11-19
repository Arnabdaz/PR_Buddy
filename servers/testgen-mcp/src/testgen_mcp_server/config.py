"""Runtime configuration for the testgen MCP server.

Resolved once from environment variables and cached (lazy singleton), mirroring
the client-config pattern used by the other PR-Buddy servers.

Environment variables:
    TESTGEN_REPO_ROOT     Absolute path to the target repository. Default: cwd.
    TESTGEN_SPEC_DIR      Repo-relative dir holding the mirrored spec tree.
                          Default: "testspecs".
    TESTGEN_COVERAGE_DIR  Repo-relative dir holding coverage artifacts synced
                          from the build machine / CI. Default: "test-results".
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    """Resolved server configuration."""

    repo_root: Path
    spec_dir: str
    coverage_dir: str


_config: Config | None = None


def get_config() -> Config:
    """Return the cached config, resolving from the environment on first call."""
    global _config  # noqa: PLW0603
    if _config is None:
        repo_root = Path(os.getenv("TESTGEN_REPO_ROOT", ".")).resolve()
        spec_dir = os.getenv("TESTGEN_SPEC_DIR", "testspecs")
        coverage_dir = os.getenv("TESTGEN_COVERAGE_DIR", "test-results")
        _config = Config(repo_root=repo_root, spec_dir=spec_dir, coverage_dir=coverage_dir)
    return _config


def reset_config() -> None:
    """Clear the cached config (test helper)."""
    global _config  # noqa: PLW0603
    _config = None
