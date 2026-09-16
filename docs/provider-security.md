# Provider capability review

Reviewed on 2026-09-07 against installed Codex CLI 0.153.4 and Claude Code 2.1.258.
Codex 0.153.4 remains the explicit fully reviewed version (`SUPPORTED`). Claude
2.1.258 remains an exact runtime requirement. Unlisted Codex versions must pass the
contract probe below before private task text is sent for assessment; passing yields
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
provider evidence is discarded. The public schema accepts the new optional evidence
field without making old saved assessments invalid.

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
