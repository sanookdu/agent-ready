# Readiness rubric v0.1

Understand the intended outcome, identify material uncertainty, distinguish owner
choices from engineering research, clarify owner intent, then consider semantic
splits. If several concerns apply, explain which condition controls the one primary
disposition and include the other concerns in risks/rationale. Do not hide an owner
choice inside a split recommendation.

| Disposition | Controlling reason | Useful next action |
| --- | --- | --- |
| READY | Coherent intent, resolved owner choices, observable acceptance, one verdict, bounded repair and available prerequisites | Hand over the cohesive unit under existing authority |
| CLARIFY | Material product/business/architecture/policy/compatibility intent is unresolved | Ask the smallest specific, answerable owner question set |
| SPLIT | Independent decision centers remain after intent is understood | Separate outcomes with independently meaningful verdicts |
| HOLD | Necessary artifact, authority, dependency or environment is unavailable | Obtain the prerequisite and reassess |

Consider governing intent; decision coherence; material intent ambiguity; owner
unknowns; implementation unknowns; independent decision centers; architectural
ambiguity; authority completeness; acceptance observability; verification coherence;
expected rejection/rework locality; external prerequisites; and material risks.

Engineering unknowns can remain in READY. Do not make users locate repository helpers
or answer questions a worker can research. The gate itself does not inspect code or
verify claims about available artifacts; it analyzes supplied evidence and should
state assumptions. Not inspecting an environment is not proof it is unavailable.

SPLIT follows semantic boundaries, not maximum task size. A 40-module migration with
one frozen compatibility promise may need one verdict and stay together. Two small
features with unrelated product decisions can require separate verdicts.

`expected_rework_locality`: HIGH means a likely rejection points to a bounded defect;
MEDIUM means repair spans coupled areas; LOW means diffuse repair across concerns.
This is a qualitative judgment about locality, not a readiness percentage. READY
never guarantees success. See the synthetic examples and the visible readiness prompt.
