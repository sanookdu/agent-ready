# Agent Ready

Stop giving coding agents bad work units. Agent Ready analyzes proposed software
work before implementation and returns a practical next action:

- **READY** — hand over cohesive, constrained, verifiable work.
- **CLARIFY** — resolve a material owner decision.
- **SPLIT** — separate independently executable or rejectable outcomes.
- **HOLD** — obtain a missing prerequisite.

**It does not make tasks smaller by default.** A large, cohesive migration can be
READY. Agent Ready assesses work; it never starts implementation.

```sh
agent-ready assess ./task.md --provider codex
agent-ready assess ./task.md --provider claude --json
```

CLI and **local MCP** use one shared assessment engine. There is no Agent Ready
backend, telemetry, central history or task collection. Task text goes to **your
selected model provider**, whose privacy and retention policies apply. See
[PRIVACY.md](PRIVACY.md).

**v0.1 is an early engineering framework**, not a scientifically validated predictor
or a guarantee of successful implementation.

## Install the release candidate

Python 3.10+ is required. From this checkout:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
agent-ready --help
```

On Windows, activate with `.venv\Scripts\Activate.ps1` in PowerShell. No Docker or
server infrastructure is required. This repository is a release candidate; these
instructions do not assume a package has been published to PyPI.

Install and authenticate one supported provider CLI separately using its official
instructions: [Codex](https://developers.openai.com/codex/cli) or
[Claude Code](https://code.claude.com/docs/en/overview). v0.1 accepts **Codex CLI
0.153.4** (analysis model `gpt-5.5`) as **SUPPORTED**. Other Codex versions are
**COMPATIBLE_UNVERIFIED** only after a credential-free local contract probe passes.
Missing/incompatible required capabilities fail closed as **INCOMPATIBLE**; a version
string difference alone does not reject a provider. Claude remains pinned to
**Claude Code 2.1.258**. The executable must be on the MCP host's PATH as well as yours.
Agent Ready uses your provider access; inference may incur provider charges. Codex
authentication uses your local `auth.json` or `CODEX_API_KEY`; keyring-only setups
are not supported in v0.1. Custom provider configurations and models are intentionally
not inherited. Claude uses its normal authentication with customizations disabled.

For GitHub input, install and authenticate `gh` separately:

```sh
agent-ready assess 'OWNER/REPO#123' --provider codex --json
```

Only that Issue's title and body are retrieved. No comments, linked artifacts,
repository scanning or mutation occurs. Local input is one explicit UTF-8 file
(up to 400,000 bytes); assessment text is limited to 100,000 characters for resource
control. This limit is unrelated to task readiness or decomposition.

Successful assessments exit 0 for all four dispositions. Errors exit 1 with no
assessment on stdout; command usage errors exit 2. `--json` prints the complete
[public contract](schemas/assessment.schema.json). Human output highlights disposition
and next action, then includes every assessment field.

## Local MCP

Run `agent-ready-mcp` as a host-managed **stdio subprocess**. It has no HTTP listener
or remote transport. Its only tool is:

```json
{"text":"Implement the approved archive compatibility migration...","provider":"codex"}
```

Call this input with `assess_work_unit`. Supply the actual text, not a path to read.
A path-like string in `text` is only text. Additional input keys are rejected.
Successful Codex results include host-measured `provider_evidence`: actual CLI
version, compatibility classification, and probe status. The model cannot supply
or override this evidence. Existing assessment fields and dispositions are unchanged.

The response has the same validated JSON object as the CLI in `structuredContent`
and a JSON text block. Failures have `isError: true` and no assessment.

Claude Desktop / hosts using `mcpServers`:

```json
{
  "mcpServers": {
    "agent-ready": {
      "command": "/absolute/path/to/agent-ready/.venv/bin/agent-ready-mcp",
      "args": []
    }
  }
}
```

VS Code `.vscode/mcp.json` uses:

```json
{
  "servers": {
    "agent-ready": {
      "type": "stdio",
      "command": "/absolute/path/to/agent-ready/.venv/bin/agent-ready-mcp",
      "args": []
    }
  }
}
```

Codex local configuration uses:

```toml
[mcp_servers.agent_ready]
command = "/absolute/path/to/agent-ready/.venv/bin/agent-ready-mcp"
args = []
```

Replace the example executable path with your installed path; on Windows use the
venv's `Scripts/agent-ready-mcp.exe`. Restart the host after configuration. Provider
MCP integrations are disabled inside assessment subprocesses, preventing recursive
Agent Ready invocation. See [local verification](docs/verification.md).

## What makes work ready?

[The rubric](docs/ready-rubric.md) separates owner choices from normal engineering
research and considers whether one independent verification verdict is meaningful.
[Principles](PRINCIPLES.md) explains the reasoning without scores or size thresholds.

Four [synthetic examples](examples/README.md) include curated JSON assessments:
[large READY](examples/ready.md), [owner CLARIFY](examples/clarify.md),
[semantic SPLIT](examples/split.md), and [prerequisite HOLD](examples/hold.md).

## Boundaries and contributions

The model receives the visible [readiness prompt](prompts/readiness.md) and submitted
text. Provider subprocesses use an empty temporary working directory, constrained
tools and isolated configuration. MCP offers no file loading, shell commands,
GitHub access, repository modification, environment enumeration or execution handoff.
Provider binaries, authentication storage and your MCP host remain trusted local
software. See [SECURITY.md](SECURITY.md) for precise limits.

Contributions and counterexamples are welcome. [CONTRIBUTING.md](CONTRIBUTING.md)
explains development and optional research consent. Use Issues for actionable bugs,
features and sanitized cases; Discussions for methodology and broader debate.
Licensed under [MIT](LICENSE).
