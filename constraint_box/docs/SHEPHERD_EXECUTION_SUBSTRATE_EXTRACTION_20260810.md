# Shepherd execution-substrate extraction for Constraint Box

Status: proposed contained design packet, extracted 2026-08-10. It adds no
dependency, provider integration, runtime authority, portable-adoption claim,
or promotion claim. It is deliberately separate from CB Heavy and from the
current 91-tool CB Light installation receipt.

## Classification

Shepherd is a candidate **external execution substrate** for short-lived,
sandboxed workers. It is not:

- CB Light's deterministic controller or finite tool domain;
- CB Heavy, a simulator, a manifold engine, or evidence for any engine claim;
- a source of truth, a semantic decider, or a replacement for CB's probe
  grammar;
- a shipped nested-council or swarm runtime.

The useful boundary is:

`CB controller and gates -> admitted provider run -> quarantined worker output -> CB verification -> CB settlement receipt`

Shepherd may make the middle segment more inspectable and more strongly
isolated. CB owns every transition before and after it.

## Extracted mechanisms

| Shepherd mechanism | CB extraction | Non-negotiable constraint |
| --- | --- | --- |
| A run is a durable record, rather than a final string. | Make a probe run the retained unit: immutable input envelope, provider settings, model route, effects, raw response, artifacts, cost, stop reason, and verdict. | A prose summary cannot substitute for the raw run record. |
| Worker effects cross an explicit boundary and are recorded. | Give every probe a typed effect ledger: model request, declared tool call, file change, network request if allowed, refusal, and artifact emission. | Missing, malformed, or unparseable effects yield `HOLD`; they are not silently omitted. |
| Output is retained beside the worktree until an explicit settlement. | Create a CB quarantine plane. A worker can propose files, JSON, or a claim packet, but cannot mutate the authoritative workspace or state spine directly. | Only the controller can emit the acceptance/rejection receipt and release an admitted delta. |
| Permissions are declared with the task rather than supplied as a drifting second policy. | Bind each probe packet to an explicit capability envelope: read roots, write roots, allowed tools, allowed network class, max cost, time budget, and output schema. | Default deny. A broadened capability envelope is a new input requiring a new receipt. |
| Jailed placement distinguishes operating-system enforcement from advisory intent. | Preserve `enforcement_mode` as measured evidence, not a label. On a compatible host, a security-relevant probe must demand native enforcement; advisory execution is a distinct, lower claim. | `auto` resolving to advisory cannot be reported as a jailed-run success. |
| Failed, exhausted, cancelled, and successful runs all retain evidence. | Treat negative probes and failed probes as first-class receipts. This is especially useful for refusal, budget, malformed-output, and prompt-injection controls. | Success counts cannot erase adverse or unresolved witnesses. |
| Changesets are inspected per named binding. | Inspect a proposed delta by bounded target before release: declared outputs, source hashes, path policy, and independent tests. | A delta outside the declared binding or output schema is rejected even if its narrative sounds useful. |
| Settlement is explicit and exactly once. | Use a controller-side terminal state rather than a mutable "accepted" boolean. | A settled run cannot be re-settled under a different claim ceiling; retries create a new run with a parent link. |

## Concrete CB provider contract

A future Shepherd adapter belongs under a distinct provider domain, for example
`execution_substrate.shepherd`; it does not enter the core CB Light library
identity merely by being installed.

The adapter input must contain:

1. `input_envelope_hash` and immutable packet bytes;
2. provider/version/lock and interpreter identity;
3. a declared placement, with `jail` required when an enforcement claim is
   requested;
4. named read/write bindings, tool/network/cost/time ceilings, and output
   schema;
5. model route, deterministic fixture or seed where applicable, and parent
   run identifier.

The adapter output must contain:

1. raw structured trace and a content digest;
2. resolved enforcement mode and permission surface;
3. outcome (`SUCCEEDED`, `FAILED`, `BUDGET_EXHAUSTED`, or `CANCELLED`), not a
   collapsed Boolean;
4. per-binding changesets/artifacts and digests;
5. measured cost, duration, and termination reason;
6. the provider's settlement state, kept distinct from CB's verdict.

CB then independently checks the payload, recomputes declared hashes and path
membership, runs the applicable probe family, records dissent/obstruction, and
emits one of `ACCEPTED`, `REJECTED`, `HOLD`, `UNRESOLVED`, or `EVALUATION_ERROR`.
Provider success is only an observation; it is never the CB verdict.

## Required vertical slice before admission

Do not add `shepherd-ai` to the current CB Light candidate roster on the basis
of this extraction. First prove one small adapter slice in a fresh isolated
environment:

1. **Artifact and install proof:** record exact package, Python, OS, and full
   closure; import and run its offline deterministic path.
2. **Positive retained-output proof:** a deterministic worker creates a
   bounded artifact in a retained changeset while the authoritative workspace
   remains unchanged.
3. **Native-enforcement negative:** with `placement="jail"`, attempt a write
   outside the declared writable binding. The run must refuse it, the trace
   must contain the refusal, and the target must remain unchanged.
4. **Advisory discrimination pair:** run the equivalent declaration in
   advisory placement and record the resolved mode as weaker evidence. CB must
   refuse to call this a native-enforcement success.
5. **Trace tamper negative:** delete, alter, or mismatch a mandatory trace or
   changeset digest. The CB adapter must return `HOLD`/`EVALUATION_ERROR`, not
   infer success from a provider summary.
6. **Release control:** show that no retained artifact reaches the real
   workspace before CB validates it and emits its own settlement receipt.
7. **Claim-boundary replay:** replay the deterministic fixture and compare the
   input, trace schema, changeset, and verdict. Any unexplained divergence is
   retained as `DRIFT` or `UNRESOLVED`.

Only after those controls pass should a live Claude-backed worker be tested.
That live lane must add prompt-injection, route/cost, cancellation, malformed
typed-output, and capability-escalation probes. It is a probe worker, not an
authority or a council controller.

## What CB should not inherit

- Do not use a task signature/docstring as the only prompt or semantic
  contract. CB still requires immutable input envelopes, typed claim chains,
  explicit assumptions, scope, countermodel attempts, and retraction
  conditions.
- Do not equate a retained changeset with an accepted claim or proof. A file
  delta is an artifact, not semantic validity.
- Do not let a provider's `select`, `apply`, or `discard` nomenclature replace
  CB's own admission and verdict vocabulary. Keep provider settlement and CB
  evaluation as separate receipts.
- Do not rely on its unshipped task-to-task delegation, durable-child, typed
  value-projection, or public replay surfaces for councils or swarm control.
- Do not use advisory placement for a claim that says operating-system
  enforcement, and do not generalize whole-repository bindings into a
  fine-grained path-policy claim without an independently tested bridge.
- Do not place Shepherd in CB Heavy merely because its workers can later call
  simulators. Worker containment and simulation are separate roles.

## Useful design language for CB

The following compact distinctions are worth retaining in the contained
controller vocabulary:

- **Run is evidence; answer is a headline.**
- **Boundary crossings are typed effects, not best-effort logs.**
- **A proposal is quarantined output, not an action.**
- **A refusal is an observed result, not an absence of work.**
- **Enforcement mode is measured fact, not configuration intent.**
- **Settlement is a single explicit transition, not a mutable flag.**

These fit the owner's probe-first, fail-closed, entropy-controlled model
without importing Shepherd's framework as CB's identity.

## Source reviewed

This packet is self-contained. The source was reviewed only to extract the
mechanisms stated above: Shepherd v0.3.0 README, effects, permissions,
placements, runs, and roadmap documentation, retrieved 2026-08-10. The
external documents are not runtime authority for Constraint Box.
