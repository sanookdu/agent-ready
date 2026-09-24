# Codex compatibility repair verification — 2026-09-16

Repair base: `14698de0c91b50725e5ff26942a3c486debd12b4`, branch `feat/v0.1`.

Exactly one harmless `agent_ready.assess_work_unit` MCP call was made after the host refresh, using provider `codex` and a synthetic exact-sentence response task. It returned `READY`, with host-generated evidence:

```json
{"provider":"codex","version":"codex-cli 0.154.0","compatibility":"COMPATIBLE_UNVERIFIED","capability_probe":"PASSED"}
```

This verifies the refreshed connection and the unreviewed-version capability path; it does not promote this version to fully reviewed `SUPPORTED` status.

## Fresh local checks

Commands executed from the Agent-Ready checkout:

- `rtk proxy /mnt/d/Projects/agent-ready/.venv/bin/python -B -m pytest -p no:cacheprovider`: exit 0, **116 passed in 36.87s**.
- `rtk proxy /mnt/d/Projects/agent-ready/.venv/bin/ruff check --no-cache .`: exit 0, all checks passed.
- `rtk proxy /mnt/d/Projects/agent-ready/.venv/bin/ruff format --check --no-cache .`: exit 0, 37 files already formatted. Initial invocation without `--no-cache` exited 2 because the sandbox denied cache writes; the no-cache check resolved that verification limitation without changing source.
- `rtk proxy /mnt/d/Projects/agent-ready/.venv/bin/python -B tests/probe_codex.py`: exit 0; actual Codex 0.154.0, required flags, one loopback request, zero tools, no private canaries, JSON output, no inference.
- `git diff --check` (inside `rtk proxy bash`): exit 0.
- `rtk proxy /mnt/d/Projects/agent-ready/.venv/bin/python -B -m build --outdir /tmp/agent-ready-compatibility-build /mnt/d/Projects/agent-ready`: exit 0 after approved execution outside the sandbox; built sdist and wheel using hatchling 1.32.0. Earlier `--no-isolation` failed because hatchling was absent; the first isolated attempt failed on sandbox DNS. Build artifacts are in `/tmp`, outside the worktree.

## MCP child lifecycle evidence

The operator reported duplicate Agent-Ready MCP children before restart. That earlier process snapshot was not independently recovered during this verification, so its exact count and cause remain unconfirmed here.

Fresh `rtk proxy ps -eo user,pid,ppid,lstart,args --width 240` returned exit 0 and showed exactly one Agent-Ready MCP server: PID 35539, parent PID 35163, started 2026-09-16 13:19:25. Its command was the checkout virtualenv Python running `agent-ready-mcp`. The Codex host PID 35163 started at 13:19:22, with launcher parent PID 35156. The other MCP children were separate Raindrop and Node MCP servers, not duplicate Agent-Ready servers.

Observed post-restart topology therefore matches one Agent-Ready server for this fresh Codex host. This snapshot does not establish a general plugin lifecycle guarantee or explain the previous duplicates. No processes were killed and no plugin configuration was changed during this verification.
