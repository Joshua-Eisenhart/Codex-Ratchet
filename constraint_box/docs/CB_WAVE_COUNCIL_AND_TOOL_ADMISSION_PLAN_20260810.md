# ConstraintBox Wave / Nested-Council and Control-Plane Tool Admission Plan

Status: proposal-only, 2026-08-10  
Scope: CB Light deterministic control plane. CB Heavy remains a separately managed simulation estate.

## The decision

ConstraintBox should not start by building a general council framework. It should first make one model-free, contained control-plane transition unavoidable:

~~~
sealed input -> strict parse -> finite decision -> bounded operation
            -> retained receipt -> independent verification -> real consumer
~~~

Only after that route exists should a wave/council be allowed to generate more candidate probe packets. A council is an exploration mechanism; it is never the authority that promotes a tool, a receipt, a claim, or a Heavy profile.

This plan deliberately uses proposed, installed locally, API-smoked, function-linked, selected for work, portable-adopted, and released as different states. No green label collapses them.

## Non-negotiable build order

The system does **not** begin by building waves.  Much of the deterministic
mechanism has already been mined and prototyped in CB, ClaimGate, and the
small CB-owned Mini-LevOS kernel.  The next task is to make the tools that
support those mechanisms cleanly installable and actually usable.

~~~
existing deterministic mechanisms
  -> clean contained CB Light tool environment
  -> exact install/import/operation evidence per candidate
  -> role-specific tool bindings into real deterministic gates
  -> one public + hook + alternate-entrypoint gate spine
  -> only then: waves of probes sent at those gates
  -> only later: nested councils and CB Heavy target profiles
~~~

Mining and source indexing may continue in parallel, but neither installs nor
new framework suggestions become integration.  A wave without an already
implemented deterministic gate is only an unconstrained discussion loop.

Skills such as premortem, loophole audit, or portability review may be used
now as bounded design/falsification help for the tool-install and gate work.
Their output is a proposal or counterexample artifact; it cannot decide a
tool's admission or substitute for an executed gate.

### Falsification safeguards

The bounded [clean-Light/gate-binding premortem](premortem-transcript-20260810T224035Z.md)
is test input for this plan, not a second authority.  Before the first cohort
moves beyond local testing, its safeguards require one protected selection
manifest, exact contained-runtime evidence, per-tool positive/negative/
boundary/replay/severance evidence, a function-level consumer, and
public/hook/alternate-route bypass negatives.  The portability matrix remains
a separate promotion condition.  A future wave may only consume the resulting
persisted gate state.

## Current, observed facts

- The current 91-row config/cb_light_tools_v1.json is explicitly proposal-only: every row has membership PROPOSED_LIGHT and adopted false. Its declared core is Z3, CVC5, SymPy, Rustworkx, and Maude.
- Pydantic is not a row in that 91-tool proposal manifest. It is declared only in the `control-plane` optional profile, not as a direct CB Light core dependency.
- Baseline inspection found that the contained mandated interpreter, constraint_box/.venv/bin/python, lacked Pydantic, Hypothesis, and jsonschema while the shared main interpreter had them. That interpreter split is recorded as a negative control, not ignored.
- The three exact pins were then installed into the contained .venv from requirements/control_plane_candidates/cb_control_plane_candidate_pins_v1.txt. The receipt at receipts/cb_control_plane_candidate_install_probe_20260810.json records the exact interpreter, closure versions, a clean pip check, strict Pydantic positive/negative, JSON Schema cross-check, canonical replay, and 32 Hypothesis-generated envelopes.
- The initial install probe earned CANDIDATE_EVALUATED_LOCAL only. The candidates remain outside the 91-row proposal, direct core dependencies, protected selection authority, portable matrix, and adoption state.
- A bounded public CLI now exists and was run as the installed console with no `PYTHONPATH` override: `constraintbox control-plane --request REQUEST --db STATE`. It strictly parses a Pydantic request, independently validates the generated schema through jsonschema, requires a current SQLite snapshot/probe/selection triple, verifies the probe interpreter matches the executing interpreter, and records only CANDIDATE_EVALUATED_LOCAL. The valid receipt attests the contained interpreter, Python, Pydantic, and jsonschema versions; the installed-console valid and capability-negative receipts are `receipts/cb_control_plane_console_receipt_20260810.json` and `receipts/cb_control_plane_console_invalid_capability_receipt_20260810.json`.
- This is an actual local function consumer, not the completed hook spine: active PreTool/PostTool still have to be deliberately migrated to the same public route and a protected selection authority still has to admit Pydantic into membership.
- The source already uses a narrow Pydantic/JSON Schema/attrs decider for a fixed name/age schema. That has no non-test inbound caller and cannot establish the requested typed controller contract.
- A SQLite-backed CB Light gate exists, and the installed `constraintbox control-plane` command consumes its selection triple. Active PreTool/PostTool configuration still routes through a separate legacy JSON receipt path, so the normal hook path and this public control-plane route remain two receipt planes rather than one unavoidable transition.

## Architecture boundary

~~~
CB Light (contained Python, deterministic authority)
  candidate identity -> strict packet -> finite gate -> receipt state -> consumer
                                             |
                                             +-- no model authority

Exploration lane (bounded, disposable)
  issue card -> wave -> independent probe workers -> typed proposal packets
                                              |
                                              +-- only packets may cross the boundary

CB Heavy (separate profiles, environments, setup/replay evidence)
  H1 profile -> engine operation -> Heavy receipt
~~~

Light does not scrape Heavy paths, system_v5, ambient package inventories, or simulation receipts to derive membership. Heavy does not borrow a Light selection receipt as proof of engine setup or operation. A future bridge is a literal typed record with both sides' IDs; it is never an import-path accident.

## Admission state machine

~~~
DISCOVERED
  -> CANDIDATE_REGISTERED
  -> PROPOSED_LIGHT
  -> INSTALLED_CONTAINED_LOCAL
  -> IMPORTED_CONTAINED_LOCAL
  -> API_SMOKED
  -> FUNCTION_LINKED
  -> SELECTED_FOR_ONE_REAL_CONSUMER
  -> PORTABLE_ADOPTED
  -> RELEASED

At every state: HOLD_MISSING_EVIDENCE | HOLD_DECIDER_DISAGREEMENT |
                REFUSED_CONTRADICTION | REVOKED_DRIFT
~~~

The only automatic direction is downward on contradictory evidence or source/environment drift. Promotion requires a distinct, stored transition. In particular, a local import, an isolated wrapper probe, a lockfile, or a green hook is not FUNCTION_LINKED.

For a tool t, the control-plane admission predicate is:

~~~
admit_for_consumer(t) =
  protected_candidate_identity(t)
  AND exact_contained_interpreter(t)
  AND pinned_install_and_provider_binding(t)
  AND real_api_positive(t)
  AND reason_specific_negative(t)
  AND one_field_boundary_flip(t)
  AND deterministic_replay(t)
  AND severance_changes_real_consumer_outcome(t)
  AND independent_validation_or_reference(t)
  AND source_consumer_hash(t)
  AND downstream_receipt_consumer(t)
  AND alternate_entrypoint_negative(t)
~~~

portable_adopt(t) adds a complete hash-bound closure and actual resolution, import, and operation on macOS, Linux, and Windows for Python 3.12 and 3.13, plus owner approval. Missing evidence is HOLD, never a synthetic pass.

## Small control-plane cohort

The following is intentionally a six-item cohort, not a new 91-package list.

| Tool | Exact present state | First permitted CB use | Current disposition |
|---|---|---|---|
| sqlite3 (Python stdlib) | SQLite gate/state code exists; the new public candidate command consumes a verified triple and writes candidate_evaluation rows. The hook path is still split. | Authoritative snapshot_id, probe_run_id, and selection_id retained state; every later provider/wave operation must consume this triple. | **FUNCTION-LINKED_LOCAL; HOLD — not yet one required hook/CLI consumer spine.** No install needed. |
| Pydantic 2.12.5 | Exact contained local install, strict API positive/negative, JSON Schema cross-check, canonical replay, real public CLI, SQLite consumer, and raw-dict severance test are receipt/test-bound. It remains absent from selection authority and pyproject.toml direct dependencies. | Strict ControlRequest, ProbePacket, WorkerResult, and ReceiptEnvelope at every untrusted boundary. | **FUNCTION-LINKED_LOCAL; HOLD_MISSING_PROTECTED_IDENTITY_AND_PORTABLE_ADOPTION.** Do not call it adopted. |
| jsonschema 4.26.0 | Exact contained local install and Pydantic-generated schema cross-check now occur inside the public consumer. | Independently validate the Pydantic-generated JSON Schema for the bounded packet types. A disagreement is HOLD. | **FUNCTION-LINKED_LOCAL; HOLD — auxiliary cross-check, not controller authority.** |
| Hypothesis 6.151.12 | Exact contained local install and 32 generated strict-envelope property cases are receipt-bound; no actual gate consumer yet. | Generate legal/illegal lifecycle packets, source-drift payloads, duplicate IDs, and single-field boundary mutations against the actual gate. | **CANDIDATE_EVALUATED_LOCAL; HOLD_MISSING_REAL_GATE_CONSUMER.** |
| Z3 + CVC5 + bounded enumeration | Declared current core candidates and used by existing finite solve paths. | Decide finite tool/wave disposition and emit counterexample/witness facts. | **FUNCTION-LINKED, but still proposal-only in the current Light manifest.** Solver agreement is not evidence truth. |
| Rustworkx | Declared current core candidate with existing finite graph role. | Enforce wave DAG and reject cycles, ancestor writes, and child-before-parent settlement. | **FUNCTION-LINKED, but no council consumer yet.** |

Keep Maude and SymPy in their current bounded formal roles. They are not required to bootstrap the first council slice. Keep fastjsonschema, PydanticAI, LangGraph, AutoGen, CrewAI, ORMs, queues, Redis, and a third SAT/ASP solver out of the first cohort: they have no necessary consumer and would create tool bloat before the deterministic spine is real.

## Pydantic's narrowly defined job

Pydantic is a good fit for strictly shaped, hostile or lossy boundary data, not for deciding semantics:

~~~
hook/provider/LLM bytes
      -> Pydantic strict model (extra=forbid, no coercion)
      -> canonical JSON + schema digest
      -> jsonschema cross-check
      -> SQLite transaction
      -> deterministic finite decision
~~~

Initial models should be small:

- ControlRequest: operation, declared purpose, exact selection triple, capability set, input digests.
- ProbePacket: target candidate, one named hypothesis, positive/negative/boundary/replay/severance case references, expected reason codes.
- WorkerResult: only artifact references, claims at an explicit ceiling, counterexamples, cost/budget use, and a declared disposition suggestion.
- ReceiptEnvelope: immutable identities, source/interpreter/policy digests, decision, and verifier result.

Required Pydantic controls:

1. Positive: a valid packet reaches the deterministic operation.
2. Negative: unknown field, missing digest, wrong enum, string-for-integer, and malformed artifact URI are refused with an exact reason.
3. Boundary: change exactly one field from an allowed capability to an undeclared capability; the route flips to REFUSE.
4. Replay: model_validate_json plus canonical serialization reproduces the same packet digest.
5. Severance: replace the Pydantic boundary with a raw dictionary in a test seam; malformed bytes must no longer cross into the SQLite decision and the consumer must HOLD.
6. Cross-check: validate the serialized packet through the generated JSON Schema with jsonschema; disagreement is HOLD.
7. Consumer: the decision must read the validated model, not a parallel raw dictionary.

Until all seven are observed under the contained interpreter, Pydantic is merely a candidate with an API smoke.

## The model-free first vertical slice

Build this before adding a council table or provider adapter:

~~~
constraintbox cb-light probe
  -> require contained interpreter and policy/source hashes
  -> create SQLite snapshot
  -> run one fixed finite tool decision
       Z3 + CVC5 + enumeration
       positive + one-field negative/boundary + replay + severance
  -> validate typed receipt
  -> store snapshot_id / probe_run_id / selection_id
  -> independent read-only verifier recomputes the decision
  -> a normal CLI transition consumes that verified selection
~~~

Implementation decisions:

1. Expose the existing cb-light-gate route through the package's normal constraintbox CLI rather than making a second decision engine.
2. Require --selection-id on every future provider, wave, council, or engine bridge launcher. Missing, stale, source-hash-mismatched, or non-admitting IDs must refuse before any child run directory or provider sidecar is created.
3. Make a single configured hook route call this public gate. Do not call the older JSON receipt path and SQLite path both active and infer a join later.
4. Move completion_allowed to a scoped fact, for example cb_light_evaluation_complete. Bare complete cannot be a system success while portable adoption remains zero or Heavy is absent.
5. Record the actual executing interpreter prefix and manifest hash. Never label a shared interpreter observation as contained just because an argument names a contained path.

The first accepted consumer may be a small library-admission operation. Its claim ceiling is only:

> One source-bound Light tool decision was deterministically reproduced and consumed.

It does not prove all 91 proposals, all platforms, CB Heavy, or a general multi-agent runtime.

## Wave and nested-council model

### What a wave is

A wave is a finite, persisted exploration batch with one issue card and a bounded frontier. It is not a conversation and not a vote.

~~~
WaveIssued
  -> PacketValidated
  -> WorkersRunning (parallel, independent)
  -> ArtifactsCollected
  -> DeterministicVerification
  -> SETTLED | HOLD | REFUSE | EXPIRED
~~~

Every row is bound to:

~~~
(run_id, wave_id, parent_wave_id, snapshot_id, probe_run_id, selection_id,
 issue_digest, policy_digest, provider_route_id, worker_budget, state)
~~~

The controller creates the issue card first. It specifies the exact unknown, finite target domain, required positive and negative probes, allowed tools, artifact sources, time/token/cost limits, stopping condition, and claim ceiling. No model can enlarge that packet.

### The first council is flat

The first council is one parent wave with three independently prompted workers:

| Role | May produce | Cannot do |
|---|---|---|
| Generator | Distinct candidate probe packets and assumptions | Set policy, choose a disposition, or write state |
| Falsifier | Counterexamples, missing assumptions, injection findings, and rejection probes | Delete evidence or override a negative |
| Evidence mapper | Source/artifact references and coverage gaps | Assert a claim without a cited artifact |

The deterministic controller, not a fourth LLM, validates schemas, enforces budgets, de-duplicates, schedules a DAG, runs tools, and settles outcomes. A model may recommend HOLD; it may never directly make ADMIT.

No nesting in v1. Enable a child council only when the parent has a source-bound, non-LLM consumer, a distinct finite subproblem, an unspent budget, and an explicit parent_wave_id. Maximum depth, total children, wall time, token cost, retries, and retained artifacts are policy fields, not prompt suggestions.

### Diversity and anti-herding controls

Council breadth is meaningful only if workers differ on declared independent axes:

- problem decomposition or controlled variable;
- source/artifact domain;
- tool capability set;
- model/provider route;
- hypothesis family; and
- explicit falsification target.

The controller stores a task-card hash and rejects duplicate issue/role/source-set/controlled-variable tuples. Workers do not see author identities, live vote totals, or a running leader summary during their initial pass. A 2025 orchestration study found authorship visibility and ongoing vote visibility can increase self-voting/herding and premature consensus; CB should treat agreement as a routing signal, not proof.

### The basin claim is measurable or absent

CB may store a finite state graph:

~~~
state_signature = digest(issue, satisfied_constraints, evidence_coverage,
                         counterexample_set, policy_version)
edge = proposal | tool_result | falsification | settlement
~~~

Call a region an observed convergence basin only after repeated, bounded runs converge to the same verified settlement under controlled perturbations of worker order, provider route, and prompt formatting. Store the perturbation matrix, transition counts, counterexamples, and non-convergent runs. Otherwise call it an unverified recurrence pattern, not an attractor or a dynamical result.

## Model-routing policy

Use lower-cost models for wide, disposable exploration; reserve frontier models for narrow architecture audits:

| Stage | Typical route | Output ceiling |
|---|---|---|
| Wave workers | Luna/Haiku; occasional Sonnet for a hard bounded task | Strict WorkerResult only |
| Synthesis/replan | Sonnet, when deterministic checks identify a real gap | New packet proposal only |
| Architecture/premortem audit | Opus/Fable/Sol, deliberately sparse | Review artifact, no direct state write |

Each call records provider route, model identity, prompt-card digest, input artifact IDs, output schema version, token/cost ceiling, timeout, and outcome. A provider sees only the sealed task card and allowed artifacts, not an unrestricted repository or mutable controller state.

## Research synthesis

- Anthropic's production research system supports the premise that independent subagents can improve breadth-first work and protect context separation, but it also reports high token costs and warns that many dependency-heavy tasks do not parallelize well. Its concrete advice—specific objectives, output formats, tools, boundaries, effort scaling, checkpoints, and observability—maps directly to Wave issue cards.  
  https://www.anthropic.com/engineering/multi-agent-research-system
- Google DeepMind's Co-Scientist uses a generated/diverse/debate/ranking/evolution cycle with a supervisor and specialized roles. That supports the shape of a generator–falsifier–evidence-mapper council, while its own discussion makes clear that automated rankings are not independent ground truth. In CB, tournaments can prioritize what to test next; deterministic evidence still decides admission.  
  https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/
- AlphaEvolve's proposal -> automated evaluator -> retained program database -> future prompt loop is the closest useful analogy for CB's probes. It supports keeping evaluated variants and feeding only scored artifacts back into later exploration. It does not support accepting an LLM proposal before robust verification.  
  https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/
- A 2025 study of multi-agent orchestration reports authorship and running-vote visibility can produce herding and premature consensus. That is a direct negative control for nested council designs.  
  https://arxiv.org/abs/2509.23537
- cvc5 supports syntax-guided synthesis and diagnostic traces of candidate solutions. That is a useful formal analogy for bounded candidate grammars and counterexamples: constrain the search grammar first, then preserve attempted candidates and the reason they fail.  
  https://cvc5.github.io/blog/2024/04/15/interfaces-for-understanding-cvc5.html
- Pydantic strict mode rejects values that would be coerced in ordinary validation, and it can generate a JSON Schema; that makes it appropriate for input/output envelopes but not a semantic solver.  
  https://docs.pydantic.dev/latest/concepts/strict_mode/  
  https://docs.pydantic.dev/latest/concepts/json_schema/
- Hypothesis is appropriate as a property-based falsifier because it generates edge cases beyond hand-written examples. Its value comes from testing the real transition, not from generating a second green artifact.  
  https://hypothesis.readthedocs.io/en/latest/

These sources motivate implementation choices; they do not prove CB's physics, attractor, or autonomous-agent claims.

## Required falsification matrix

| Attack / mutation | Required outcome |
|---|---|
| Pydantic absent from contained interpreter | HOLD_MISSING_CONTAINED_INSTALL; no raw-dict fallback |
| Extra field / type coercion / invalid enum | Exact packet rejection before SQLite transition |
| Pydantic removed at consumer seam | No accepted decision; consumer HOLD |
| Pydantic-vs-jsonschema disagreement | HOLD_DECIDER_DISAGREEMENT |
| Missing/stale selection_id | No provider/wave child is launched and no sidecar is written |
| Direct alternate CLI route | Same gate result as the normal route |
| Hook config routes legacy JSON but not SQLite gate | End-to-end configuration test fails |
| Recomputed SQLite/receipt tamper | Read-only verifier rejects the selection |
| One-field capability change | Exact REFUSE_UNDECLARED_CAPABILITY boundary flip |
| Council workers use same source set/controlled variable | De-duplication rejects or merges them before launch |
| Running votes/author identity leaks | Test fixture confirms workers receive neither |
| Worker finds a negative counterexample | It remains retained and cannot be overwritten by a majority |
| Heavy interpreter/profile appears in Light envelope | REFUSE_LIGHT_HEAVY_BOUNDARY |
| Any missing matrix cell (OS × Python) | HOLD_NOT_PORTABLY_ADOPTED |

## Ordered implementation plan

1. **Freeze membership and lifecycle authority.** Add a protected, owner-approved selection manifest that is the only authority for membership. Candidate registry, lockfiles, installed metadata, and local probe results are distinct inputs/outputs.
2. **Unify the contained Light route.** The public local candidate route now consumes the SQLite triple. Next expose the complete cb-light probe|verify|status command and route active hooks to it or label legacy hooks telemetry-only.
3. **Make Pydantic a real candidate.** The exact contained local installation/probe receipt and real local consumer now exist. Next add a protected candidate identity and full hash lock; it is still not adopted.
4. **Bind the first real consumer.** Done for the deliberately narrow candidate-evaluation operation: ControlRequest feeds a Pydantic/jsonschema boundary, SQLite records the triple-bound local outcome, and a raw-dict severance test holds. Extend this exact pattern to the first selected operational tool, not to a generic council.
5. **Add Hypothesis to falsify the actual route.** Do not create a generic fuzz harness; generate lifecycle and boundary packets for that same consumer.
6. **Add the flat three-worker wave.** The wave can create candidate packets only after the first consumer is passing. No nested council, no provider framework, and no Heavy operation yet.
7. **Run portable adoption matrix.** macOS/Linux/Windows × Python 3.12/3.13, each under the exact hash-bound closure with import and real operation receipts. Until then, every relevant tool is locally evaluated only.
8. **Add nesting only from evidence.** Require a passing parent-to-child consumer edge, novelty/deduplication metrics, fixed budgets, and a real use case where one wave cannot make progress.

## Definition of done for the first milestone

- One exact interpreter is bound into all Light receipts and no shared/Heavy environment is mislabeled as Light.
- One normal CLI route, one hook route, and one direct alternate route all consume the same verified selection triple.
- Pydantic's strict boundary changes the real consumer outcome under a severance negative.
- SQLite is authoritative for the three IDs; JSON/JSONL is an export, not authority.
- The first selected tool has a positive, reason-specific negative, one-field boundary, replay, severance, independent validation, and downstream receipt consumer.
- Missing/stale/tampered evidence produces HOLD or REFUSE, never generic completion.
- The system still says only one CB Light control-plane transition verified. It makes no Heavy, portability, attractor, or general-autonomy claim.
