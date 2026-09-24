# Claude Code compatibility probe: independent review record

Candidate branch: `fix/claude-capability-probe` (base `6b05681`).
Change: replace the exact Claude Code `2.1.258` pin with a reviewed-version set plus a
credential-free loopback capability probe (`agent_ready/claude_compatibility.py`).
Agent Ready does not use pull requests. This file is the durable review record, and
accepted work lands by direct merge preserving the accepted candidate SHA.

Each review was independent: a fresh reviewer that did not write the change, working
read-only. Its experiments ran the real Claude Code `2.1.281` only against a loopback
endpoint, with a placeholder key.

## Review 1: candidate `2f6ac21`, REPAIR_REQUIRED

| # | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | BLOCKING | The probe ran under a synthetic home but the assessment ran under the user's real home, so a future CLI could pass the probe while the assessment loaded host hooks, settings or MCP servers. Hooks never reach the wire. The reviewer demonstrated a hook capturing private task text. | Repaired in `ba32ea8`: the assessment runs in an isolated home holding only the copied credential file. |
| 2 | MATERIAL | Docs overclaimed; HEAD, PUT, DELETE and OPTIONS returned 501 unrecorded. | Repaired in `ba32ea8`, completed in review 2's repair. |
| 3 | MINOR | Only `tools` was checked, not other tool channels. | `mcp_servers` and `container` refused (a documented denylist). |
| 4 | MINOR | Several checks had no discriminating test. | Tests added. Each check mutation-tested. |
| 5 | MINOR | Handler threads were not joined. | Threads joined; the join is bounded in review 2's repair. |
| 6 | MINOR | macOS Keychain precedence unverified. | Documented limitation. |
| 7 | MINOR | Codex-probe schema reader transition undocumented. | Documented. |

## Review 2: candidate `ba32ea8`, REPAIR_REQUIRED

| # | Severity | Finding | Disposition |
|---|---|---|---|
| N1 | MATERIAL | The home seeds were placed in the original home, which isolation hides from the CLI, so user-scope flag behaviour was no longer tested per version. The docs presented it as tested. | Repaired: the isolated home the CLI runs under is also seeded. Real `2.1.281` with `--setting-sources ""` and `--safe-mode` removed fires the isolated-home and project hook tripwires and is refused. With the flags intact it passes. |
| 2 (open) | MATERIAL | TRACE, CONNECT and custom methods still got 501 unrecorded. | Repaired: every method without a handler is refused and recorded. |
| N2 | MINOR | Only POST bodies were inspected: not headers, query strings or a HEAD body. | Repaired: method, path with query, and headers of every request are inspected. A HEAD with a body is refused. |
| N3 | MINOR | Joining non-daemon handler threads could stall without limit on a trickling client. | Repaired: a 10-second total body-read deadline. Test: a trickling client fails the probe in about 1 s with the deadline, and takes 8.1 s (test fails) with the deadline removed. |
| N4 | MINOR | An OAuth refresh-token rotation inside the isolated copy could invalidate the stored credential. Untested. | Documented limitation, shared with the Codex adapter. |
| 4 (open) | MINOR | No `container` or ignores-base-URL tests. | Added, with a positive control for the MCP tripwire. |

Mutation evidence for this repair: removing the isolated-home seeding, the any-method
refusal, the HEAD body check, header and query inspection, the `container` key, or the
MCP tripwire each fails at least one test. The explicit deadline check at the top of the
read loop is a redundant second guard: the per-read socket timeout is already capped at
the remaining time, and removing both mechanisms fails the trickle test.

## Review 3: candidate `e4bf7bc`, ACCEPT

No BLOCKING or MATERIAL finding remained. Every prior finding was verified against the
code, the tests and the real `2.1.281` CLI. Two were only partial:
- R1-5/N3: body reads are bounded, but the header phase is not.
- N2: a repeated header and an over-long request line are not fully inspected.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | MINOR | Commit messages overstate test counts. `2f6ac21` adds 23 tests, not 26 (122 → 145). `e4bf7bc` adds 10, not 13 (157 → 167). | Corrected here; history not rewritten. |
| 2 | MINOR | The 10 s deadline covers bodies only; trickled header lines held the probe for 30 s. Fails closed. | Docs narrowed. Header deadline deferred as follow-up. |
| 3 | MINOR | Only the first value of a repeated header is inspected; a >64 KiB request line gets a stdlib 414 unrecorded. | Documented limitation. Deferred follow-up. |
| 4 | MINOR | Same MCP server name in every scope, so project shadows user scope. The user-scope MCP tripwire is not independently exercised. | Documented limitation. Deferred follow-up (distinct names per scope). |
| 5 | MINOR | SECURITY.md said the listener serves "one synthetic request". | Corrected. |
| 6 | MINOR | Recording of unparsable requests (`if ok else None`) has no discriminating test. | Deferred follow-up. |
| 7 | MINOR | The probe exercises API-key auth only, not the claude.ai OAuth path. | Documented. |

The accepted candidate for landing is `e4bf7bc` plus this docs-only commit, which records
this review and narrows the documentation. No code or test changes were made after the
ACCEPT.
