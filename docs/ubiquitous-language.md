# Agent Ready Ubiquitous Language — v0.1

**Status:** v0.1 — first canonical pass, reconciled against the frozen v0.1 specification
(`docs/agent-ready-v0.1.spec.md`), the public assessment schema
(`schemas/assessment.schema.json`), the visible readiness prompt (`prompts/readiness.md`),
`PRINCIPLES.md` and the current implementation — subject to evidence-driven refinement.

This document names the concepts Agent Ready owns. It defines nothing on behalf of any consumer:
a consumer that records, retains or acts on an assessment names *its* concepts in *its* own
language and references these terms. Where a proposed term collided with an established term in
the specification or schema, the established term wins and the collision is recorded in §3.

## 1. Product boundary

Agent Ready is a local-first, provider-neutral, analytical readiness gate. It owns readiness
semantics, the four dispositions, assessment logic and analysis dimensions, the public versioned
assessment contract, the CLI, the local MCP interface, its provider adapters, and backward
compatibility of its public interface. It executes nothing, mutates nothing, and holds no
implementation, planning, work-management or lifecycle authority. **READY is advice, not an
execution trigger or authorization.**

## 2. Terms

**Assessment** — A durable result of applying Agent Ready readiness semantics to one identified
Work Unit under one identified version/provider context: exactly one Disposition plus the
required analysis fields of the Assessment Contract. Produced identically by the CLI and the MCP
tool from one shared engine.

**Work Unit** — A proposed unit of autonomous software-development work supplied to Agent Ready
as text for assessment. Agent Ready places no requirement on what a consumer calls it or how it
is tracked; task size is not LOC, file count, component count or hours.

**Readiness** — The degree to which a Work Unit is sufficiently understood, cohesive, constrained,
prerequisite-satisfied and verifiable for autonomous implementation. Qualitative in v0.1: there
is no score, percentage or weighted formula.

**Disposition** — Exactly one terminal semantic assessment outcome: `READY`, `CLARIFY`, `SPLIT`,
`HOLD`. A Disposition is an assessment result. It is not a lifecycle, planning or
work-management state of any consumer system, and consumer vocabulary is never projected back
into it.

**READY** — The Work Unit is sufficiently coherent and constrained to hand to an autonomous
implementation agent. Requires clear intent, resolved owner decisions, acceptable decision
coherence, observable acceptance, one meaningful independent verification verdict, bounded
rework and available prerequisites/authority. Engineering research may remain. READY does not
guarantee success and is not execution authorization.

**CLARIFY** — Material owner intent is unresolved; the smallest useful set of specific,
answerable owner questions must be resolved before responsible implementation. Not used for
ordinary engineering research the worker can perform itself.

**SPLIT** — The Work Unit contains materially independent decision centers whose combination
creates unnecessary implementation or verification risk; separation is recommended at semantic
or decision boundaries. Never triggered merely because the work is large.

**HOLD** — A required external prerequisite — artifact, environment, dependency, permission,
decision or capability — is absent or unavailable. HOLD is not unresolved owner intent; that is
CLARIFY. Not inspecting an environment is not proof it is unavailable.

**Governing Intent** — The one dominant reason a Work Unit exists. Multiple implementation
activities are acceptable when they derive from the same governing intent.

**Owner Unknown** — Something that cannot responsibly be inferred through engineering research
because it depends on product, business, architecture, policy, compatibility, authority or other
owner intent. An Owner Unknown normally produces an **owner clarification** (schema field
`owner_clarifications`), the question put to the owner.

**Implementation Unknown** — Something a competent implementation agent should research or
derive during execution without changing owner intent or authority (schema field
`implementation_unknowns`). Never escalated to the owner.

**Prerequisite** — An external condition, artifact, environment, dependency, permission,
decision or capability that must exist before implementation can responsibly begin. Its absence
controls HOLD.

**Independent Decision Center** — A part of a Work Unit that can be implemented, accepted or
rejected, or reasoned about independently enough that combining it with the rest materially
increases rework or decision coupling (schema field `independent_decision_centers`).

**Decision Coherence** — Whether a Work Unit's important decisions are meaningfully coupled;
coupled decisions stay together, independently rejectable ones are candidates for SPLIT.

**Verification Coherence** — Whether independent review can deliver one meaningful verdict on the
Work Unit (schema field `verification_assessment`).

**Rework Locality** — How well likely implementation/verification repair remains confined to the
Work Unit: `HIGH` localized, `MEDIUM` coupled areas, `LOW` diffuse (schema field
`expected_rework_locality`). The specification also calls this *rejection locality*; the two
names denote one concept. It is not a probability of success.

**Split Boundary** — A semantic boundary recommended between Independent Decision Centers
(schema field `semantic_split_recommendation`). It is advice; Agent Ready never restructures a
consumer's plans, items or dependencies.

**Assessment Contract** — The public JSON Schema (`schemas/assessment.schema.json`) that every
successful assessment satisfies, shared by CLI and MCP; malformed provider output fails closed
and never becomes READY. In v0.1 the contract is versioned by the package release (`0.1.0rc1`);
the schema carries no separate version identifier (§3).

**Provider Evidence** — Host-measured facts about the provider that produced an assessment
(`provider_evidence`: provider, CLI-reported version, compatibility classification, capability
probe status). The model cannot supply or override it; schema validation checks its shape, not its
origin. In v0.1 it is emitted for Codex only.

**Assessment Feedback** — Attributable downstream outcome evidence supplied by a consumer and
linked to the assessment that preceded it. *Roadmap concept:* v0.1 defines no feedback contract;
the closest existing surface is the "Share an assessment case" Issue template, which is manual
and consent-gated.

**Feedback Corpus** — A versioned set of Assessment Feedback used to evaluate and improve
readiness semantics. *Roadmap concept:* v0.1 keeps no central or local history by design (spec
§14). Improvement, when it exists, stays governed: evidence → candidate lesson → evaluation →
versioned rule/prompt/model change → independent validation → release. Agent Ready never
mutates readiness rules autonomously from individual feedback events.

## 3. Collisions and gaps recorded

| Proposed term | Established term / fact | Resolution |
|---|---|---|
| Owner Question | Spec §3.5 *Owner Unknown*; schema `owner_clarifications` | *Owner Unknown* is the condition; *owner clarification* is the question it produces. "Owner Question" is not adopted. |
| Engineering Unknown | Spec §3.5 and schema *Implementation Unknown* (`implementation_unknowns`) | Established term wins; "Engineering Unknown" is not adopted. |
| Rework Locality | Spec §3.7/§5 *rejection locality*; schema `expected_rework_locality` | One concept, two names; schema name is canonical. |
| Split Boundary | Schema `semantic_split_recommendation`; spec "semantic boundaries" | Adopted as the noun for one recommended boundary; schema field holds the list. |
| Assessment Contract "versioned" | Schema has no version field; package version is the only version identity | Gap recorded: consumers must retain the package version alongside the raw assessment. A schema version identifier is a candidate compatibility improvement, not a v0.1 change. |
| Provider provenance | `provider_evidence` is Codex-only and rejects `provider: claude` | Gap recorded: Claude assessments carry no host-measured provenance in v0.1; consumers must record provider/model themselves. |
| Assessment Feedback / Feedback Corpus | Not in v0.1 (spec §14, §36) | Roadmap; no interface exists. Any consumer-side feedback emission has nothing to target yet. |
| BLOCKED / NEEDS_CLARIFICATION / SPLIT_RECOMMENDED | Not Agent Ready terms | A consumer's own or historical vocabulary; never a Disposition. |

## 4. Not in this language

Anything about a consumer's lifecycle (states such as READY-as-a-lane, IMPLEMENT, DONE),
work-management items, planning, allocation, execution, verification verdicts or repository
mutation. Agent Ready assesses; it does not do any of those things.
