# Privacy

Agent Ready has no operated backend, central telemetry, central usage database,
central assessment history or central task-content collection. It does not retain,
sell or use task content to train an Agent Ready-controlled model.

Task text is processed in the local process and submitted over stdin to the Codex
or Claude CLI you explicitly select. That CLI may send the text to its model
provider. The provider's own privacy, retention and training policies apply; Agent
Ready makes no promise about third-party behavior. Your provider access pays for
any inference charges.

CLI file input reads only the explicitly supplied task file. GitHub input invokes
your authenticated local `gh` for one Issue's title and body. MCP accepts text only;
it never obtains files, Issues or linked pages on your behalf.

Agent Ready does not write assessment history or archive raw tasks. Temporary runtime
directories are removed after provider invocation. Codex runs with an isolated home;
only its fixed local `auth.json` authentication artifact is copied into a private
temporary configuration directory (when present), never included in model input.
No user instructions, skills or configuration are copied. Its original credential
file is not updated, so expired credentials may require authenticating Codex again
outside Agent Ready. Adapters request ephemeral
Codex sessions / no Claude session persistence and disable provider telemetry controls
where supported. Provider software may still maintain its own local authentication,
logs, caches or other state. Your shell, terminal, MCP host, operating system and
provider can retain content independently; deleting or controlling that state is
outside Agent Ready. Crash cleanup is not a secure-erasure guarantee.

Only an explicit allowlist of runtime and provider authentication environment values
is inherited by provider subprocesses. These values are not exposed as MCP inputs or
outputs. Provider errors are sanitized rather than echoing their logs or task text.

GitHub Issues and Discussions are public community submissions, not automatic
collection. Sanitize them before posting. Research reuse of contributed cases
requires the optional affirmative permission described in CONTRIBUTING.md. Feedback
without permission is welcome for maintenance and discussion.
