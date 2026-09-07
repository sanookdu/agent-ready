# Agent Ready v0.1 implementation plan

Authority: `agent-ready-v0.1.spec.md`, frozen and unchanged. Work stays on
`feat/v0.1`. The non-interactive mission authorizes normal implementation decisions.

Architecture: a Python assessment engine consumes text and a provider adapter,
then validates against the public JSON Schema. CLI source conveniences are separate
from the stdio-only MCP server. Providers receive delimited data over stdin with
execution capabilities disabled. No history, telemetry, hosting, or extra providers.

- [x] Contract and engine: retain existing contract tests, add hostile-input and
  strict JSON cases; implement `contracts.py` and `engine.py`, public schema/prompt.
  Run pytest before and after implementation; commit the passing core.
- [x] Provider and source boundaries: exercise injected subprocess errors, exact
  commands, timeout, isolation, local UTF-8 files and explicit Issue parsing.
  Implement `providers.py` and `sources.py`; verify provider capability controls
  against installed CLIs before any model call.
- [x] Interfaces: implement argparse CLI and SDK stdio MCP; test all dispositions,
  malformed requests/output and real protocol enumeration with fake inference.
- [x] Public artifacts: README, principles, rubric, privacy, security, contribution
  guidance, MIT license, four synthetic task/result pairs, Issue templates and CI.
- [x] Verify: complete suite, help, representative fake CLI assessments, MCP startup,
  enumeration, schema, wheel install outside checkout, lint/diff and content scans.
- [x] Independent second-agent review required by spec section 30; permit one
  bounded repair cycle. Record scope audit and remaining release gates.
Delivery: commit logical work and push the current branch; no merge, tag, or release.
The final handoff records the actual pushed SHA.

The specification has damaged formatting in sections 11, 23, and 36; overlapping
explicit CLI/MCP boundaries and non-goals elsewhere resolve these without changing
product intent. Its actual filename differs from the mission spelling.
