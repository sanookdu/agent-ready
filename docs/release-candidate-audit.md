# v0.1 release candidate scope audit

Date: 2026-09-07. Authority: the unchanged founder-approved
`agent-ready-v0.1.spec.md`. Version: `0.1.0rc1`. Branch: `feat/v0.1`.

## Scope coverage

| Frozen specification | Implementation and evidence |
| --- | --- |
| 1–5, 39: governing intent and readiness semantics | Shared engine and visible prompt; rubric and principles; four curated synthetic cases |
| 6: complete structured contract | Public Draft 2020-12 schema, runtime jsonschema validation, strict JSON parsing; invalid output never produces a disposition |
| 7, 11–12: explicit CLI sources | One UTF-8 file or exact Issue reference; title/body-only gh invocation; no recursive analysis |
| 8, 22, 26: local MCP | SDK stdio server; only assess_work_unit(text, provider); same engine/output; real protocol tests and local host examples |
| 9–10, 20, 24–25: providers and security | Thin constrained Codex/Claude subprocess adapters; text-only model capabilities; private runtime state; sanitized errors; no arbitrary tool execution |
| 13–14: privacy | No backend, telemetry, central history, task collection or archival feature; provider policy and local-provider-state limits documented |
| 15, 27–28: community | All three Issue forms; research checkbox required:false; no-consent maintenance/reuse distinction documented; Issues and Discussions enabled remotely |
| 16–19, 23: public artifacts | Required documentation, MIT license, public schema/prompt, install metadata, synthetic task/result pairs and tests |
| 21, 29: verification | Full offline suite, provider wire probe, real CLI inference, real MCP inference, build and independent installed-wheel checks |
| 30: independent review | ACCEPT from a second coding agent; no blocking findings; credential-environment tightening separately rechecked and accepted |
| 31–35: founder review, publication and maintenance | Founder release review remains a human gate; no public release or promotional posting performed; maintenance policy documented |
| 36–38: scope and priority | No v0.2 features, hosted service, web UI, background daemon, database, automatic execution, extra providers or repository indexing |
| 40: developer experience | Installable CLI and local MCP both return one validated disposition, rationale and concrete next action |

The specification's damaged formatting in sections 11, 23 and 36 is resolved by
its repeated explicit boundaries and governing statement, without editing it.
The specification file's existing name uses `.spec.md`.

## Verification results

- `.venv/bin/python -m pytest -o addopts='' -q`: **85 passed in 39.40s**.
  No live model calls are made by the suite.
- Independent reviewer: full 83-test suite before final credential refinement;
  all 25 boundary tests after it, including both new credential-isolation cases.
- `ruff check .` and `ruff format --check .`: passing.
- CLI help and assess help: exit 0.
- Test-only CLI subprocess helper: READY, CLARIFY, SPLIT, HOLD each exit 0;
  malformed output exits 1 with empty stdout and a schema error on stderr.
- `python tests/probe_codex.py`: PASS with the actual pinned binary; one loopback
  request, zero model tools, no private instruction/skill canaries, no inference.
- Live installed CLI, synthetic READY task: Codex 0.153.4 with gpt-5.5 and Claude
  Code 2.1.258 both exit 0 and return schema-valid READY, no owner questions and no
  split recommendation. These manual smoke calls are separate from the test suite.
- Live stdio MCP with Codex, synthetic session-migration task: schema-valid CLARIFY;
  owner cutover decisions and serializer/adapter implementation research separated.
- Normal isolated `python -m build`: source archive and wheel built. Clean wheel
  installation in `/tmp/agent-ready-wheel-verify`, outside the source checkout:
  CLI help, bundled prompt/schema equality, all four fixture validations and real
  stdio MCP initialization/tool enumeration passed. Final artifact is rebuilt after
  the last source change and reinstalled before delivery.
- Four GitHub YAML files parsed; optional permission checkbox checked programmatically.
- Repository scans: no prohibited private-project references outside the exempt
  frozen specification; no credential/private-key signature matches. These scans
  supplement source review, not a mathematical guarantee about arbitrary secrets.
- Frozen specification diff is empty. Whitespace/diff checks pass.

## Independent verdict

**ACCEPT — current v0.1 release candidate. No remaining blocking findings.**
The reviewer independently checked contracts, boundaries, semantics, examples,
privacy, consent, tests, lint, Codex wire capabilities and installed-wheel resources.
The main agent supplied live model and installed-MCP evidence. Acceptance is for the
reviewed implementation, not authorization to publish or a guarantee of model accuracy.

## Limitations and release gates

No required v0.1 implementation item is known to be unmet. Founder review and public
release remain intentionally unperformed. No merge, release tag or public v0.1.0
release is part of this mission.

Provider compatibility is pinned to the reviewed versions. Codex uses gpt-5.5 and
supports a local auth.json or CODEX_API_KEY, not keyring-only/custom-model setups.
Provider credentials, administrator policy, provider binaries and MCP hosts remain
trusted. Provider policies govern remote processing. Unit fixtures do not validate
arbitrary LLM reasoning or establish predictive accuracy.

Local execution verification used Linux/WSL and Python 3.12. Other platform runtime
behavior was not manually verified; CI covers additional Python versions. GitHub CI
results and final pushed SHA are reported in the implementation handoff rather than
assumed from local evidence. This file contains no private task examples or inference
transcripts.
