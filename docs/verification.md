# Local verification

Install `.[dev]` as described in CONTRIBUTING.md, then run:

```sh
python -m pytest
agent-ready --help
agent-ready assess --help
ruff check .
ruff format --check .
python -m build
```

The tests use fake subprocess boundaries and curated synthetic assessments; no paid
model is invoked. Real stdio MCP client/server tests verify initialization, tool
enumeration, text-only argument validation, all four dispositions, shared-engine
schema validation, malformed output and provider failure for both adapter selections.
No filesystem resources or prompts are advertised.

Representative CLI runs without inference:

```sh
python tests/helpers/fake_host.py cli ready assess examples/ready.md --provider codex --json
python tests/helpers/fake_host.py cli clarify assess examples/clarify.md --provider claude
python tests/helpers/fake_host.py cli split assess examples/split.md --provider codex
python tests/helpers/fake_host.py cli hold assess examples/hold.md --provider claude
python tests/helpers/fake_host.py cli malformed assess examples/ready.md --provider codex --json
```

The last command must exit 1 with empty stdout and an error on stderr. The helper is
test-only; no fake provider is exposed through the installed product.

With the exact supported Codex binary installed, the optional offline capability
probe needs no authentication or paid inference:

```sh
python tests/probe_codex.py
```

For manual MCP verification, configure a local host using README.md, enumerate tools
and confirm only `assess_work_unit`. Call it with the *contents* of a synthetic example
and explicit provider. Expect the public assessment JSON or an `isError` response;
never file retrieval. These manual calls use your provider and may incur charges.
A real inference smoke test is a release gate separate from deterministic tests.

To check the wheel independently of the checkout, install the built wheel in a fresh
venv, change to an unrelated empty directory and run `agent-ready --help`. Import
`agent_ready.contracts.SCHEMA` and validate a synthetic JSON assessment there; the
wheel must contain the public prompt and schema as package resources. Run MCP stdio
initialization from that same environment.
