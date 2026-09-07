# Contributing

Start with a reproducible problem or sanitized assessment counterexample. This release
is intentionally small: one shared engine, CLI, local text-only MCP and two providers.
No hosting, telemetry, automatic implementation or repository-wide analysis.

Use Python 3.10+ and an isolated environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install '.[dev]'
python -m pytest
ruff check .
ruff format --check .
python -m build
```

Tests must not invoke paid models. Inject the subprocess boundary and exercise actual
contract validation and CLI/MCP behavior. Synthetic expected assessments demonstrate
semantics; they are not tests that an arbitrary model always reasons identically.
Changes to provider controls require a capability review of the exact supported
version. Keep the public schema and prompt authoritative; both interfaces share them.

Use Issues for defects, actionable feature requests and assessment cases. Discussions
are for broader debate and methodology feedback; suggested categories are General,
Ideas, Assessment Cases and Show and Tell. Maintenance prioritizes reproducible bugs,
provider/MCP compatibility, privacy/security defects and evidence of incorrect
readiness reasoning. Feature requests are evidence, not obligations.

All shipped examples must be synthetic and free of private or proprietary material.
Sanitize submitted cases yourself; never include credentials or private business data.
The assessment-case form contains **optional research permission**. You can submit
feedback without checking it. Without affirmative permission, feedback can inform
normal maintenance and discussion, but maintainers must not intentionally incorporate
it as a case into a research dataset, published example or publication. Affirmative
permission allows the uses specified by that checkbox. Do not infer consent from
filing an Issue or leaving the box unchecked.

Contributions are under the MIT license. The founder-approved v0.1 specification is
frozen; report contradictions rather than rewriting product intent. Implementation
changes require independent review before release. Do not publish releases as part
of ordinary contribution or test workflows.
