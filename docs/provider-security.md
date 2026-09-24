# Provider capability review

Reviewed on 2026-09-07 against installed Codex CLI 0.153.4 and Claude Code 2.1.258.
Codex 0.153.4 and Claude Code 2.1.258 are the explicit fully reviewed versions
(`SUPPORTED`). Unlisted versions of either provider must pass the contract probe below before private task text is sent for assessment; passing yields
`COMPATIBLE_UNVERIFIED`, not a claim of full version review. No minimum-version
comparison or permissive version wildcard substitutes for capability evidence.

Codex needs more than read-only sandboxing: shell tools can read files, global
instructions can load despite `--ignore-user-config`, and model metadata can expose
`apply_patch`. The adapter isolates its home/configuration, copies only the fixed
authentication artifact into private temporary state, disables capability features,
and uses a minimal text-only `gpt-5.5` model catalog with no patch capability. Its
original authentication file is not modified. Keyring-only authentication and custom
models/configuration are not supported by this adapter.

For each assessment using an unlisted Codex version, the adapter checks the required
CLI flags and exercises its constrained command against a temporary loopback fake
Responses endpoint. No user authentication or task text is passed to the probe.
Synthetic original-home instruction/skill canaries exercise the same empty-home
isolation helper as production. The probe requires exactly one request, `tools: []`,
the intended model and synthetic prompt, no canary leakage, successful exit, and the
expected JSON stdout. It never invokes live inference. It uses a 10-second help
limit, 30-second subprocess limit, bounded HTTP reads, and closes the listener.
A failed or unavailable probe blocks inference; its failure is not an authentication
diagnosis. Results are not cached solely on version strings.

`python tests/probe_codex.py` runs this same probe explicitly against any installed
Codex, including reviewed versions. CI can test the contract with synthetic provider
runners and needs no installed provider CLI. Built-in provider instructions or
metadata may still be present; those differ from private host instructions.

The reviewed-version set currently contains only `codex-cli 0.153.4`; 0.154.0 has
passed the new offline probe but is intentionally classified as
`COMPATIBLE_UNVERIFIED`. Real provider smoke assessments are separate evidence.
Successful Codex assessments carry host-generated `provider_evidence` with the
actual version and compatibility/probe status. INCOMPATIBLE has no assessment;
failures remain sanitized and never become READY/HOLD results. Model-supplied
provider evidence is discarded. `REVIEWED_VERSION` means no runtime probe was run
because the reported version is in the reviewed set; `PASSED` means this invocation's
probe passed. Only `SUPPORTED/REVIEWED_VERSION` and `COMPATIBLE_UNVERIFIED/PASSED`
validate. Schema validation checks shape only: it cannot authenticate that a saved
document's evidence was host-measured rather than edited later.

## Claude Code

Claude Code 2.1.258 was previously an exact runtime requirement: any other version
failed before submitting content, although no incompatibility had been demonstrated.
On 2026-09-24 Claude Code 2.1.281 was observed to accept every adapter flag and to
return schema-valid assessments, so the exact pin rejected a working provider while
proving nothing about the boundary it stood for. It is replaced by the same
reviewed-set-plus-probe policy as Codex.

The boundary has two layers. First, both the assessment and the probe run Claude Code
under an **isolated temporary home** that contains only the copied credential file
(`.claude/.credentials.json`, if present), so user settings, hooks, MCP servers
(`~/.claude.json`), instructions, skills, agents, commands, output styles and plugins
are never present. This is the same pattern as the Codex adapter. Second, the flags
(`--tools ""`, `--safe-mode`, `--setting-sources ""`, `--strict-mcp-config` with an
empty MCP configuration, `--disable-slash-commands`, `--no-session-persistence`,
`--permission-mode dontAsk`) exclude project-level customizations in the working
directory, which a home change cannot isolate.

For each assessment using an unlisted Claude Code version, the probe checks those flags
appear in `--help`. It seeds three places with every customization class above
(instruction, skill, agent, command and output-style canaries, plus settings hooks and
MCP servers whose commands create tripwire files):
- an untrusted original home, which exercises the same isolation helper as the
  assessment;
- the isolated home the CLI then actually runs under, so the flags are tested at user
  scope for each version rather than assumed from the home change;
- the project directory.
It then runs the unmodified assessment command against a temporary loopback fake Messages endpoint
(`ANTHROPIC_BASE_URL`) with a fixed non-secret placeholder key and no assessment
credential. The probe fails if any of the following holds:
- a tripwire file exists afterwards (a hook or MCP server executed locally);
- any request of any HTTP method is anything other than a strictly decoded
  `POST /v1/messages`, except a body-less `HEAD /api/hello` connectivity check
  observed from the real CLI;
- any request carries non-empty `tools`, or a top-level `mcp_servers` or `container`
  key (other ways the Messages API attaches tools);
- a canary appears in a request body, a request path including its query string, or
  the first value of a request header; or the synthetic prompt does not appear in a
  request body;
- the process exits non-zero, or stdout is not the expected JSON.

The loopback server joins its handler threads before the checks run. Each request
body must arrive within a total 10-second deadline. The header phase has no total
deadline: a local client that keeps trickling header lines can hold the probe open
until it stops. This fails closed, since nothing is sent while the probe waits. The probe never
invokes live inference, and uses a 10-second help limit and a 60-second subprocess
limit.

What this does not prove: the check on top-level tool keys is a denylist of known
channels, not an allowlist, so a future tool channel under a new key would not be caught
by it. `tools: []` and the isolation layers still apply. On macOS, Claude Code may read
credentials from the Keychain, which is not tied to the home directory; the probe
relies on the placeholder `ANTHROPIC_API_KEY` taking precedence there, which has not
been verified on macOS. The probe exercises the API-key authentication path only; the
claude.ai OAuth path is not exercised, although a placeholder OAuth token was observed
to produce the same requests on 2.1.281. Only the first value of a repeated header is
inspected, and a request line longer than 64 KiB is rejected by the HTTP layer before it
is recorded. Every seeded scope names its MCP server `private`, so the project entry
shadows the user-scope one, and the user-scope MCP tripwire is not exercised
independently; the assessment home carries no MCP configuration. With subscription OAuth, a token refresh during an assessment
is written to the temporary credential copy, which is then deleted. If the provider
rotates refresh tokens, the stored credential could be invalidated. This is untested,
since testing it needs real credentials. The Codex adapter's copied `auth.json` has the
same property. If a CLI ignored `ANTHROPIC_BASE_URL`, the synthetic prompt
would go to the real API with the placeholder key, be refused, and fail closed; no task
text or credential is sent.

Negative controls observed against the real 2.1.281 CLI on 2026-09-24: removing
`--tools ""` sends the full tool list; removing `--setting-sources ""` and
`--safe-mode` leaks the instruction canaries and fires both the isolated-home and
project hook tripwires, and is refused by the probe.
Successful Claude assessments now carry host-generated `provider_evidence` with
`provider: "claude"`; the schema binds each provider to its own version format.
The reviewed-version set contains only `2.1.258 (Claude Code)`.

Contract transition: the optional field keeps old saved assessments valid, but a reader
that validates with the earlier schema (`additionalProperties: false`) rejects every
enriched Codex or Claude result. Readers that adopted the unreleased Codex-probe
schema (`provider` fixed to `codex`) likewise reject Claude results and must accept
`claude`. Readers must tolerate the optional field. The v0.1 contract is
versioned by the package release; a result-level product/schema version identifier is
tracked separately (issue #1) and is not part of this change.

The probe itself never receives copied credentials or task text; the `--version`
discovery that precedes it runs in the assessment environment with the copied
`auth.json`, and the probe's decoding of the wire request is as strict as assessment
output decoding (duplicate keys and non-JSON constants are rejected).

Claude's installed help documents `--tools ""`, `--safe-mode`,
`--strict-mcp-config`, empty settings sources and disabled slash commands. The
adapter combines these with no Chrome, no session persistence and an empty working
directory. Safe mode disables global/project customizations while retaining local
authentication; administrator-managed policy remains part of the trusted provider.
Both adapters use an explicit environment allowlist and never expose credentials to
MCP or interpolate task content into command arguments.

References used to check controls:

- [Codex configuration](https://developers.openai.com/codex/config-reference)
- [Codex CLI reference](https://developers.openai.com/codex/cli/reference)
- [Claude CLI reference](https://code.claude.com/docs/en/cli-reference)
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

Local `--help`, the installed executable and the offline wire probe are the direct
compatibility evidence. Full reviewed support and runtime compatibility are distinct.
The probe does not attest a compromised binary or prove every future CLI behavior.
Authentication, read-only sandbox selection, tool restrictions, isolated homes,
private auth-copy handling, and the environment allowlist remain mandatory.
