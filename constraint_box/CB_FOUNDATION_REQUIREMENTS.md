# Constraint Box foundation requirements

Status: contained working contract, extracted 2026-08-10. This document states the requirements that the current `constraint_box` implementation must satisfy. It is not a claim that every later layer is already implemented.

## Authority and intake

The authority order for this extraction is:

1. Verbatim owner rulings and owner prompts.
2. Live contained source, configuration, executed controls, and receipts for implementation-status claims.
3. `constraint-box.md`, both August 6 semantic-drift revisions, and the constraint-stack audit/repair record as proposal or defect material. The semantic-drift documents label themselves proposed and non-canonical; they supply implementation candidates, not owner canon by their own assertion.
4. The recent `CB_START_HERE.md`, `CB_WORK_ORDER.md`, and `CB_UPGRADE_WORK.md` handoffs and other model-authored summaries as routing only. Their claims do not override owner rulings and do not count as runtime evidence.

The Desktop `Constraint Box` tree, wiki, chat handoffs, and archives are intake sources only. The runtime must not import them, read them as authority, or depend on their paths. Useful requirements are restated here and implemented inside this folder.

## Product identity

Constraint Box is a deterministic, finite-domain admission, orchestration, and audit harness placed around probabilistic LLM work. It does not make an LLM deterministic. It constrains what inputs enter a run, which probes are required, which outputs are admissible, what remains unresolved, and what evidence a controller may consume.

The owner's declared design bias is operationalist, nominalist, and sentimentalist: no unearned universal or causal story, probe-relative identities, and empirically real recorded sentiments. This is a design orientation for the harness, not a claim that CB has proved a philosophy. Formal names and equations must accompany project nicknames in load-bearing tables and contracts. Identity is always relative to a declared probe family, written `a ~_P b`; axes do not silently collapse.

The native work unit is a probe packet, not a single linear answer. A gate opens a bounded field of competing probes. Probes may map several plausible paths and attractor-like basins, but an attractor or causal interpretation is not inferred from static compatibility alone.

LLMs propose, normalize, critique, search, and generate rival probes. Deterministic code owns admission, rejection, replay, receipt binding, and completion decisions. A producer never certifies its own output.

## Light and Heavy are separate products

### CB Light

CB Light is the lean controller and Python-library tool estate. Its current install slice is:

- one finite proposed-root manifest;
- an exact root lock for the current macOS/Python 3.13 execution lane;
- a clean-environment install and a contained-runtime verification;
- per-tool functional probes with positive, negative, boundary, replay, severance, and reference evidence;
- deterministic selection and explicit `HOLD` results;
- hook adapters and a contained install broker;
- receipts consumed by later gates.

Mostly-Python does not mean pure Python. Native-wheel libraries such as `rustworkx`, Z3, and cvc5 may be Light when they are direct deterministic controller capabilities and pass the Light constraints.

The Light dependency domain has two literal role layers. Core controller-runtime candidates may define the deterministic constraint, graph, parsing, or symbolic machinery used by the product. Supporting probe, test, audit, serialization, integrity, and engineering candidates may be installed and selected for bounded work without thereby becoming CB Light's runtime identity. Tool membership, work selection, runtime identity, and portable adoption remain separate fields; the presence of test or build tooling in the evaluated estate does not collapse those fields.

CB Light must ultimately install and operate on maintained Python versions across macOS, Linux, and Windows. A successful macOS/Python 3.13 lane is a current local execution result, not satisfaction of the cross-platform product requirement. Platform-unavailable or untested rows remain `HOLD` for portable use.

### CB Heavy

CB Heavy is the simulation-engine estate and its explicit bridge contracts. JAX, PyTorch, Julia, Maude-based simulation lanes, manifold engines, and other engine orchestration are not silently absorbed into the CB Light install set merely because they can build or test CB.

Build tools, test tools, proof tools, sim engines, ClaimGate, Codex Ratchet, promotion, and release remain separate claim ceilings. An adapter between them must be explicit, versioned, and receipt-bound.

No path, module, receipt, or label named `system_v5` is part of the CB Light identity.

## Finite-domain tool selection

The controller must distinguish, never conflate:

- discovered environment distributions;
- top-level installed distributions;
- transitive dependencies;
- registry candidates;
- proposed roots;
- rejected candidates;
- currently selected tools;
- held tools;
- portable/adopted tools.

Cardinality is not membership. The proposed set must be derived from declared source files, be unique under normalized distribution names, and be sealed with the exact source and implementation hashes. Changing one member or one constraint requires a new manifest identity.

Current-work selection requires measured facts, not a package name or an import alone:

1. Exact locked root version is installed in both the mandated contained runtime and a newly created clean environment.
2. The resolved import file belongs to the declared distribution and the process prefix being measured.
3. The clean dependency closure is complete for the active marker environment.
4. A fresh subprocess executes a real API operation.
5. A reason-specific negative control observes the declared refusal or behavioral difference.
6. A boundary pair straddles the same semantic edge.
7. Replay is deterministic for the bounded fixture.
8. Import or provider severance actually removes the capability being tested.
9. A bounded reference is independently derived, or the row is honestly held.
10. Probe structure is non-vacuous and the consumer recomputes facts from raw evidence.
11. The receipt is fresh, source-bound, environment-bound, and consumed by the selection gate.

Missing evidence yields `HOLD`; it is not converted to success. A failing candidate may be excluded before installation. A current-work selection is not portable adoption. Portable adoption additionally requires platform resolution and operation, artifact hashes bound into a full closure lock, size budgets, security and license review, bypass controls, a production caller/output edge, and owner approval.

`promotion_allowed = false` is the standing default at every layer. Installation, selection for current work, adoption, integration, proof, promotion, and release are distinct transitions.

## Probe grammar

Every load-bearing bridge or tool capability needs a finite probe family appropriate to its claim:

- positive control;
- reason-specific negative control;
- boundary pair;
- hostile or malformed input where relevant;
- deletion or severance control;
- mutation control;
- metamorphic control when equivalent representations exist;
- independent recomputation or a declared lack of reference;
- deterministic replay.

The wide probe set must include multiple crossings and non-crossings of the same boundary, not one successful example. A controlled twin changes one load-bearing variable at a time. A probe is creditable only if the capability under test discriminates the outcome; merely calling a library while some other field decides the verdict is hollow integration. Cheap independent tools should recompute the same bounded claim, and backend disagreement is retained rather than voted away.

A negative control that fires is a successful probe. A negative that was expected to refuse but passes is a gate failure. Therefore a suite reporting only passes, with no exercised refusal outcomes, is evidence of missing discrimination rather than blanket success. Majority vote and scalar scores do not erase divergent witnesses. `UNRESOLVED`, `HOLD`, `PARKED`, `BLOCKED`, `INCOMPARABLE`, `EVALUATION_ERROR`, `UNKNOWN`, `REFUSED`, `UNAVAILABLE`, `INSUFFICIENT_DEPTH`, `INVARIANT_VIOLATION`, and `DRIFT` remain distinct information-bearing states with an obstruction and a re-offer condition.

## Semantic and claim-type firewall

The controller keeps these relations typed separately:

- admission or compatibility relation;
- distinguishability demand;
- minimal sufficient structure or plural frontier;
- ranking or utility relation;
- agent policy and action interface;
- causal or dynamical claim;
- representational encoding;
- universal or necessity claim.

A filter is not an optimizer. A Boolean encoding is not a utility identity. A representation is not the represented object. A plural admissible frontier does not imply a single winner. Static compatibility does not establish attractor dynamics, causality, agency, or universal necessity.

Any type escalation needs an explicit bridge packet with finite controls, a countermodel attempt, declared scope, an independent verifier, and a retraction condition. Without it, retain the narrower result and return `HOLD` or `PARKED` for the stronger claim.

## Controlled inputs and claim movement

The larger August 6 semantic-drift revision contributes a useful proposed control-plane design. It does not become canon merely because it is detailed. The contained system retains these parts as queued implementation requirements because they directly support the owner's prompt-, context-, and injection-control requirements:

1. **Artifact custody:** prove the named bytes, paths, versions, locks, and manifests exist before interpreting them.
2. **Input admission:** issue an immutable input envelope naming the exact source bytes, definitions, prior commitments, allowed bridges, question, and requested output mode for one bounded evaluation.
3. **Semantic contract:** extract a typed claim chain, ambiguity set, scope, new assumptions, and requested bridges without letting the normalizer choose a convenient narrative.
4. **Evidence and execution:** bind the operation, environment, controls, raw observations, and independent recomputation to a bounded receipt.
5. **Release and promotion:** derive the maximum allowed claim and re-offer condition; keep promotion a separate fail-closed transition.

Exploration and controlled evaluation are different lanes. Free prose, rival theories, analogies, and new terminology may enter an exploration annex, but they cannot mutate controller commitments or release state. A controlled proposal must cite its input-envelope hash and premise identifiers, declare new assumptions, provide a typed claim chain, attempt a finite countermodel, state scope and a retraction condition, and request a bounded claim ceiling. The raw model response remains audit evidence; only the validated typed packet can reach a deterministic gate.

The proposed semantic commitment ledger is evaluation-scoped, not a truth ledger. “Locked” means immutable for that bounded evaluation. An acknowledgement in prose does not update it, and a producer cannot launder an unregistered premise or a renamed blocked bridge into the next step. Proposed fixtures `CB-SD-001` through `CB-SD-012` are retained as a future adversarial test family for filter/optimizer collapse, encoding/identity drift, forced scalar settlement, acknowledgement reversion, input leakage, status laundering, and handoff/version fiction. None is claimed implemented by the present dependency slice.

## Ratchet and process order

CB is a ratcheting process, not a bag of independent gates. Each rung declares its predecessor state, permitted transition, non-commuting alternatives, required probes, obstruction states, and receipt. Advancing a rung revalidates the earlier gates and receipts it depends on. If changing the order changes the admissible result, that non-commutation is recorded rather than normalized away; associativity is not assumed where it has not been tested.

A loop must advance a declared state, produce a receipt, revise an obstruction, or terminate. Repetition without a measured delta is a dead loop. A later rung cannot retroactively certify an earlier one, and a downstream layer cannot be hidden evidence for its own prerequisite. The initial dependency slice is one rung only; it does not yet implement the full process-order state machine.

## Councils, waves, and model context

Councils are structured probe generators and critics, not voting authorities. A council member may itself be a council; the intended system supports at least three nested council layers, with bounded skills, agents, and tools beneath them. Horizontal and vertical waves must advance a declared question, emit receipts, and terminate or re-offer. A loop that only repeats prose is a dead loop.

Members of one council answer the same bounded question under genuinely different salience, roles, tools, or MMMs; splitting one question into unrelated subtasks is not debate. Councils run multiple rounds, may loop vertically within their nesting and horizontally back to earlier waves, and preserve dissenting witnesses. Member counts and round counts are declared per run; the earlier measured conformance floor of five members is retained as a proposal to test, not silently treated as owner-minted law.

Input diversity is measured on the variable prompt stratum rather than diluted by the conserved preamble and shared context. Voices, skills, formal agents, roles, and deterministic tools are reusable members and must be represented in coverage as member × role × wave, not merely listed in a registry.

MMMs and role prompts supply pre-language saliency biases. They shape what a model notices but do not become controller rules. Large contextual materials may be loaded into short-lived workers, while lean typed prompts and strict output schemas are passed between stages. This controls context rot and prompt-injection surface without pretending to predetermine the answer.

Lower-cost models may be used broadly for bounded probes. Frontier models are reserved for synthesis, adversarial audit, or disputed high-level bridges. Model outputs remain untrusted proposals regardless of model tier.

Every model call records model identity, route, token/cost budget, actual burn, stop reason, and parent work unit. Cheap-model lateral spread is allowed where it reduces elapsed time or increases probe diversity, but a controller must enforce per-wave and per-run ceilings and refuse unbounded retries. Frontier-model use is an exceptional audit transition, not a default worker route.

CB may carry lean, explicitly labeled approximations of manifold, predictive-modeling, FEP, engine-stage, or attractor-basin structure to shape probes and councils. “Resemblance” is not import authority, simulation evidence, or proof: full engine workloads and their receipts remain CB Heavy or later layers.

## Retained state

SQLite is the contained retained-state foundation for exact run and receipt queries. At minimum, the future state spine must distinguish runs, ratchet rungs, waves, councils, council members, roles, skills, voices, tools, probes, artifacts, verdicts, parent receipts, obstructions, re-offer conditions, model routes, and burn accounting.

The index is a pointer and comparison surface, not a verdict authority. It reduces irrelevant context and locates artifacts; the controller must read and verify the artifact before making a load-bearing claim. Producer booleans are stored as producer assertions, never promoted to controller verdicts by ingestion.

JSON and JSONL may remain interchange or export formats. They do not substitute for the authoritative, transactionally updated state spine.

## Hook and completion boundary

Hooks must make the intended route easy and the guarded transitions unavoidable within the configured Claude Code lifecycle:

- `SessionStart` validates the contained contract and reports the exact state.
- `PreToolUse` refuses recognizable direct dependency mutation and points to the contained broker.
- `PreToolUse` also blocks direct `Edit`, `Write`, and `NotebookEdit` mutation of the contained environment, authoritative receipts, hook controller, and hook settings.
- `PostToolUse` remeasures after Bash and file-edit tools; `PostToolBatch` is an additional end-of-batch observation and must not be presented as a guaranteed model-repair channel.
- `PostToolUseFailure` records failed broker attempts.
- `TaskCompleted`, `SubagentStop`, and `Stop` cover separate completion paths. A recursive Stop invocation is allowed to return without re-blocking so the hook cannot livelock the session.
- `ConfigChange` revalidates hook wiring.
- `FileChanged` records reactive observations for named authority files. Claude Code defines this event as non-blocking, so it is evidence and warning only, never the enforcement claim.

Command-string parsing is only an early warning. It cannot prove that a shell program will not mutate an environment. The postcondition is the real gate: remeasure the installed distribution set and versions, hash the complete persistent site-packages file set (including unowned modules and `.pth` files), rerun contained import resolution, and compare all three with a broker-produced receipt. Host hooks are not an operating-system or server-side security boundary, and this limitation must remain explicit.

Project hooks load only when Claude Code recognizes this repository as the project root. A contained launcher starts Claude from that root, and actual event receipts distinguish “configuration is present” from “a hook fired.” Starting Claude elsewhere, disabling project hooks, or mutating the host outside Claude's hook lifecycle is outside this project's enforcement boundary and cannot be disguised as covered.

The hooks themselves require positive, refusal, compound-command, bypass, failure-path, source-drift, receipt-tamper, runtime-mutation, replay, and completion-blocking probes. Missing or malformed hook configuration fails the guarded transition; it does not silently fall back to an unguarded claim.

## Source, receipt, and self-application rules

- Contained implementation sources and their exact set are hash-bound.
- Receipts record run identity, aware timestamps, interpreter prefix, platform, source hashes, input receipt hashes, raw observations, recomputed facts, and bounded claim ceiling.
- Aggregates are recomputed from rows; stored counts or booleans are never trusted merely because they are present.
- A clean-install receipt must be generated during the current install run and must prove its imports came from that clean prefix.
- The full transitive closure and artifact hashes must be locked before any reproducible or portable-install claim.
- Every gate is run against its own shipped artifact. Described-but-absent files, undeclared files, stale manifests, empty measurement sets, and version divergence fail closed.

## Layer order

The dependency order is:

`Constraint Box -> Sim Engines -> Manifold -> degrees of freedom -> engines -> Holodeck`

Later layers may provide probes to an earlier layer but may not be used as hidden authority to declare that earlier foundation complete.

## Current implementation ceiling

The present work implements and verifies only the CB Light tool-installation vertical slice. It does not yet implement the SQLite wave/council state machine, the full nested-council orchestration, CB Heavy, sim-engine bridges, the manifold, promotion, or release. Those are next layers, not hidden meanings of the current 91-tool receipt.
