# Provider capability review

Reviewed on 2026-09-07 against installed Codex CLI 0.153.4 and Claude Code 2.1.258.
These exact versions are runtime requirements, not promises about later versions.

Codex needs more than read-only sandboxing: shell tools can read files, global
instructions can load despite `--ignore-user-config`, and model metadata can expose
`apply_patch`. The adapter isolates its home/configuration, copies only the fixed
authentication artifact into private temporary state, disables capability features,
and uses a minimal text-only `gpt-5.5` model catalog with no patch capability. Its
original authentication file is not modified. Keyring-only authentication and custom
models/configuration are not supported by this adapter.

`python tests/probe_codex.py` exercises the actual adapter and installed binary
against a loopback fake Responses endpoint. It supplies synthetic instruction/skill
canaries and verifies one request with `tools: []`, neither canary in model input,
and no live inference. Built-in provider instructions/environment metadata may still
be present; these are different from user repository or global instruction content.
The probe is opt-in because CI need not install provider CLIs.

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

Local `--help`, the pinned executable and the offline wire probe are the direct
compatibility evidence. Documentation can change; do not broaden version acceptance
without repeating the capability review. This does not attest a compromised binary.
