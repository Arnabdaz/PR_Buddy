# testgen-mcp

MCP server providing the **deterministic core** for spec-driven unit test
generation. The intelligent work (writing specs, generating tests) is done by
the agent (Claude) following the `generate-unit-tests` skill; this server
supplies the reliable, testable plumbing:

- **Gap detection** — for a package or a set of changed files, report per-symbol
  `has_test` / `has_spec` / `spec_fresh` / `coverage`.
- **Spec store** — read/write human-reviewed specs in a mirrored tree
  (`testspecs/…`), with symbol-scoped fingerprints for freshness.
- **Coverage parsing** — Go `.coverprofile` (Jest lcov later) → per-file/per-symbol coverage.
- **Path mapping & commands** — source → test/spec paths; the exact test/coverage
  command to run on the build machine or in CI (this server never runs builds itself).

See the design doc for the full architecture (shared engine + skill; local +
GitHub-Action drivers).

## Layout

```
src/testgen_mcp_server/
├── app.py          FastMCP singleton
├── server.py       entry point (--transport)
├── config.py       env-driven config (TESTGEN_REPO_ROOT, TESTGEN_SPEC_DIR, …)
├── tools.py        @mcp.tool() wrappers (thin; delegate to engine)
├── specstore.py    mirrored-spec read/write + fingerprint + freshness
├── engine/         gap detection + orchestration
└── adapters/       base.py (contract) + registry.py + go.py (+ typescript.py later)
```

## Develop

```bash
./setup.sh          # uv sync
uv run pytest       # unit tests
uv run testgen-mcp  # run the server (stdio)
```

Configure via env (see `setup.sh`): `TESTGEN_REPO_ROOT` must point at the target
repository (e.g. cloudera-sense).
