# Security

Agent Ready is analytical. READY is advice, not an execution trigger or authorization.
The application never runs implementation commands, changes repositories or Issues,
commits, pushes, deploys, or retrieves arbitrary URLs.

## Capability boundary

The MCP server exposes exactly `assess_work_unit(text, provider)` over local stdio.
It registers no resources or prompts and accepts no paths, shell commands, environment
queries or provider configuration objects. It does not import CLI source loaders.
The only allowed providers are `codex` and `claude`. Unknown keys and malformed inputs
are rejected before inference. A string that resembles a path remains uninterpreted
text. Provider selection is explicit because inference sends content outside the
process to the user's chosen provider.

Task text is hostile data. A visible rubric and JSON-encoded delimiters resist prompt
injection but cannot guarantee correct model judgment. Security primarily comes from
removing capabilities: stdin input, argument arrays with `shell=False`, empty temporary
working directories, an environment allowlist, no inherited provider customizations,
and disabled model tools/connectors. Subprocesses have timeouts. Schema validation
rejects incomplete objects, unknown enums, extra fields, wrong types, empty prose,
non-JSON constants, duplicate keys and Markdown-wrapped JSON. Failures never become
READY (or fabricated HOLD). Human terminal output removes control characters.

Codex uses read-only sandboxing, no approvals, ignored user configuration/rules,
an isolated home with only a private temporary auth-file copy, a fixed `gpt-5.5`
text-only model catalog removing patch tools, zero project-document allowance,
disabled shell/image/browser/connector/plugin/hook/
memory/agent features, and ephemeral sessions. Claude uses an empty tool set, safe
mode, no slash commands, strict empty MCP configuration, no settings sources,
no Chrome and no session persistence. These are fixed adapter choices; task text
cannot change them. A read-only shell alone would not protect private file contents.

## Trust and compatibility

The installed provider binaries, their runtime, local administrator policies, local
credentials and the MCP host are trusted. Agent Ready is not an OS sandbox for a
malicious provider executable or compromised host. Its Python process must load its
own package, public prompt/schema and dependencies; this is not model-directed file
access. Provider software must read authentication and may keep its own state.

For v0.1 the supported versions are exactly Codex 0.153.4 and Claude Code 2.1.258.
Unknown versions fail before submitting content. Version strings are compatibility
checks, not binary attestation. Adapter updates require renewed capability review,
including a local fake-provider wire probe, since flags and default tools can change.
Managed provider policies may cause a safe error; never remove controls to work around
one. See [provider evidence](docs/provider-security.md).

The input/output limits and 180-second inference timeout bound ordinary usage, not
all denial-of-service risks. This is a trusted local subprocess integration, not a
multi-tenant service. There is no HTTP server or background daemon to expose remotely.

## Reporting

Use the repository's private vulnerability reporting feature when available. If it
is unavailable, open a minimal Issue requesting a private contact without posting
exploit details or secrets. Never submit credentials, private task text or private
repository content. Report supported-version capability regressions as security bugs.
