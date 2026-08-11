# CB Light Wave Research and Practices

Status: research-backed working plan, 2026-08-10.  It is neither a new owner
canon nor evidence that a general wave runtime, provider route, portability
matrix, CB Heavy profile, or tool adoption is complete.

## Decision in one sentence

**CB Light can run formal nested waves now; a CB Heavy or simulation engine is
not a prerequisite.**  Here “formal” means that the *management and
settlement mechanics*—topology, bounds, packet validation, deterministic gates,
state, receipts, replay, and refusal—are executable and constrained.  It does
not mean that model prose, council agreement, a route label, or a solver result
about an incorrectly encoded formula becomes authoritative.

The correct first use is a small, local, deterministic fixture wave around an
already bounded CB Light decision.  It establishes an enforcement seam for
future LLM/tool probes; it is not a claim that every asset must run in a wave.

## Authority and evidence hierarchy

| Rank | Material | What it controls here | What it does **not** establish |
|---|---|---|---|
| 1 | Current owner directions and [`WIZARD_WAVE_MODEL_OWNER_CANON_20260806.md`](WIZARD_WAVE_MODEL_OWNER_CANON_20260806.md) | The desired nested shape: wave → council set → council → member council → skills/formal agents; different MMMs and constrained inputs; waves as sequential barriers. | A particular framework, a current runtime call path, or a completed portability/adoption claim. |
| 2 | Current CB Light source and exercised receipts | What this checkout actually validates and consumes.  In particular, the contained control-plane function validates a typed request, binds it to selection state, and returns the literal local ceiling `CANDIDATE_EVALUATED_LOCAL`. | General councils, a provider worker, a full 91-tool proof, or portable adoption. |
| 3 | [`MINILEVOS_AND_WAVE_MODEL_CLARITY_AUDIT_20260810.md`](MINILEVOS_AND_WAVE_MODEL_CLARITY_AUDIT_20260810.md) and the existing tool-admission plan | Useful source-bound working design and guardrails: Light/Heavy separation, finite probe semantics, receipt-first admission. | Owner canon where it conflicts with rank 1. |
| 4 | [preserved Lev nested-wave patch context](../../../wiki/codex-memory/context_packets/2026-06-23-lev-nested-wave-council-management-patch/README.md) and historical package/skill registries | Candidate mechanisms and vocabulary to mine: management plane, receipt management, routing, context loading, and explicit recipes. | An applied Lev decision or runtime proof; the context packet explicitly says it is preserved, not applied. |
| 5 | External engineering/research sources below | Design patterns and falsification hypotheses. | CB law, semantic truth, a solver encoding, or a reason to add a dependency without a consumer. |

This ordering resolves a recurring category error: a generated plan, a
historical patch, an installed distribution, a code symbol, an LLM review, and
a replayed controller transition are different kinds of evidence.

## Boundaries that must remain literal

### CB Light and CB Heavy

CB Light owns a portable, mostly-Python control plane.  It can issue, bound,
record, verify, and settle a wave without importing a simulator.  CB Heavy is a
separately profiled, CB-managed simulation estate.  A later Light wave may
target a Heavy bridge, but Heavy interpreters, packages, engine receipts, and
completion claims do not silently supply Light authority.

### Wave, council, probe, and gate

| Term | Bounded meaning | Not equivalent to |
|---|---|---|
| **Probe** | One finite operation or evidence request with declared inputs, allowed capabilities, budget, artifact contract, and negative cases. | A vote, a loose agent task, or proof by narrative. |
| **Gate** | Deterministic code/tool transition over sealed inputs and retained evidence. | A model judge, a score, or a green import. |
| **Wave** | A persisted, bounded set of probes around a particular deterministic gate, with a barrier before its next state. | The whole CB tool stack. |
| **Council** | A role-structured grouping within a wave.  It may nest as owner canon describes. | A parliament that manufactures truth. |
| **MMM** | A versioned, provenance-bound context/saliency slice. | Global mutable memory, policy, or a verdict. |
| **Formal agent** | An adapter that executes a declared deterministic procedure (for example, a finite solver query or a verifier). | A label on a model call. |

One package, skill, MMM, formal agent, or provider can take more than one role.
Conversely, a role may use several assets.  Classification is therefore a
property of a **binding and invocation**, not of a package name.

## The Light-only first fixture

The immediate implementation target is a *local fake-adapter fixture*.  Its
purpose is to falsify scheduling, receipt, and gate assumptions before a real
model provider or a new orchestration framework makes diagnosis expensive.

```text
sealed IssueCard
  -> strict ProbePacket envelope
  -> controller-fixed WaveRecipe + DAG preflight
  -> CouncilSet / Council / MemberCouncil bindings
  -> local deterministic fake adapters emit WorkerResult artifacts
  -> typed artifact validation and evidence collection
  -> finite deterministic gate + read-only replay verifier
  -> SETTLED | HOLD | REFUSE | EXPIRED receipt
```

The fixture should contain at least one structural instance of the owner’s
nested shape, such as one wave, one council set, one council, and three member
councils (operation/witness, falsifier, and evidence mapper).  Each member can
initially have one local deterministic adapter.  This checks ancestry, bounds,
dependency order, artifact custody, and settlement without falsely claiming
that an LLM council, an MMM preload, or a skill execution occurred.

The controller, not an adapter, must create the `WaveRecipe`, choose terminals,
set depth/child/time/token/cost/artifact limits, bind the selection snapshot,
and decide whether a state transition occurs.  A fake or provider worker may
only return a typed candidate artifact.  It cannot write authoritative state,
grow the DAG, replace policy, erase a retained counterexample, or promote an
asset.

### Minimum fixture contracts

| Contract | Required fields or checks | Why it exists |
|---|---|---|
| `IssueCard` | issue ID/digest, finite target domain, stated unknown, claim ceiling, required probe families, source/artifact allowlist, selection/snapshot binding | Prevents models from turning an issue into an unbounded research program. |
| `WaveRecipe` | stable wave ID, parent ID if any, fixed topology digest, roles, maximum depth/children/retries/cost/time/artifacts, terminal states | Lets a verifier reject model-authored or mutated flow graphs. |
| `ProbePacket` | task card digest, adapter capability set, input roots, one hypothesis, positive/negative/boundary/replay/severance case IDs | Makes each probe testable rather than merely descriptive. |
| `WorkerResult` | immutable artifact IDs/digests, declared observations, counterexamples, consumed budget, adapter identity, suggested disposition only | Preserves useful output without delegating authority. |
| `WaveReceipt` | policy/source/interpreter/tool/provider/adapter digests; topology; ancestry; all results; gate reason; verifier result; claim ceiling | Supports independent replay and refusal of drift. |

The exact Pydantic boundary is appropriate at these untrusted data crossings:
strict validation rejects unwanted coercion, and Pydantic can generate a JSON
Schema for an independent structural cross-check.  That is an envelope guard,
not semantic solving or a substitute for a gate.  [Pydantic strict mode](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/) and [Pydantic JSON Schema](https://pydantic.dev/docs/validation/latest/concepts/json_schema/).

## Many-to-many asset bindings, without invented execution

Store an explicit binding record rather than a one-column “tool belongs to
wave” label.  A suitable identity is:

```text
(wave_id, council_id, member_council_id, binding_id,
 asset_kind, asset_id, asset_version_or_digest, purpose, invocation_mode)
```

`asset_kind` includes `skill`, `mmm`, `formal_agent`, `tool`, `provider`, and
`source_pack`.  `purpose` can include generation, falsification, source mapping,
tool operation, topology checking, gate verification, maintenance, or
observation.  `invocation_mode` distinguishes reference-only data from an
actual execution.

Each binding needs one of these *separate* states:

| Binding state | Minimum evidence |
|---|---|
| `DESCRIBED` | Registry/config text only. |
| `BOUND_REFERENCE` | Immutable version/digest and declared purpose, but no execution. |
| `INVOKED` | Adapter receipt names the task card, exact asset identity, input digest, exit/outcome, and output artifact. |
| `VERIFIED_RESULT` | The deterministic consumer read the retained result and the independent verifier accepted its effect. |

This follows the existing registry rule that a described member is not a run
member until a receipt binds spec, task card, MMM/slice preload, runtime,
output, and proof depth.  It prevents “we used skills/MMMs” from becoming a
claim made solely because they appear in a registry.

## Diversity is provenance, not node count

Nested topology creates *places* for independence; it does not create
independent evidence by itself.  Three member councils that share a prompt,
MMM, source roots, adapter, model route, and live synthesis are one evidence
line in three receipts.

For every non-deterministic probe, retain at least these root identities:

```text
issue_digest
task_card_digest
mmm_digest (or explicit NONE for deterministic workers)
prompt_template_digest
source_pack_and_artifact_root_digests
tool_capability_set_digest
adapter_build_digest
provider_route_and_model_identity
seed_or_deterministic_run_nonce
parent_artifact_ids
```

The controller should calculate a provenance matrix before settlement:

1. Reject exact duplicate `(role, controlled variable, source-root set,
   hypothesis family)` work unless explicitly marked as a replay.
2. Classify shared roots and correlated outputs as `CORRELATED`, not as
   corroboration.
3. Hide author identity, running vote totals, and a rolling leader synthesis
   until the initial independent pass is sealed.
4. Run clone and severance controls: duplicate an adapter/input path, then
   remove or perturb one claimed-independent root.  The receipt must show the
   relationship changed rather than merely a different child ID.
5. Preserve a falsifier counterexample as protected evidence.  Later agreement,
   ranking, or synthesis cannot erase it.

The resulting metric is not “number of agents”; it is a bounded report of
which evidence roots are shared, distinct, unavailable, or contradicted.

## Deterministic settlement and formal-tool practice

The first gate should use a finite, declared problem and emit the formula/input
digest, theory, tool version, solver result, witness or unsatisfiable core when
available, and a deterministic enumeration result where the domain permits it.

- Z3 is a solver component for logical formulae; cvc5’s Python quickstart
  explicitly exposes `sat`, `unsat`, and `unknown`, witnesses, and unsat cores.
  [Z3 Guide](https://microsoft.github.io/z3guide/docs/logic/intro/) and
  [cvc5 Python quickstart](https://cvc5.github.io/docs/latest/api/python/base/quickstart.html).
- Cross-solver agreement is a useful **diagnostic**, not independent proof if
  both consume the same incorrectly encoded model.  The encoding/theory digest,
  expected domain, negative formula, and enumeration witness must be retained.
- An `unknown`, incompatible theory, missing solver, mismatched witness, or
  missing bound is `HOLD`, never a synthesized success.
- Rustworkx (or a small equivalent deterministic graph verifier) should check
  a fixed DAG, ancestor restrictions, and child-before-parent settlement.
- SQLite is the authority for row identities and append-only evidence; JSON or
  JSONL may be an export, never a replacement authority.

This makes model/council output **proposal input** to a gate.  No majority,
ranking tournament, LLM judge, model “confidence,” or role title can change a
gate verdict.  At most it chooses which permitted probe to run next.

## Required falsification and replay matrix

| Mutation or probe | Required result |
|---|---|
| Valid sealed packet and expected witness | Only the declared deterministic transition proceeds; receipt is retained. |
| Extra field, coercible wrong type, invalid enum/capability, malformed artifact reference | Refusal before state mutation or child launch. |
| Change exactly one allowed capability, ancestry relation, or source digest | Exact reason-specific `REFUSE`/`HOLD`; no broad “failed” result. |
| Cycle, unknown node, child-before-parent settlement, or model-authored successor | DAG/policy preflight refusal. |
| Reuse a purportedly idempotent identity with different parent/child material | Immutable-state error and rollback/savepoint behavior; no partial record. |
| Rerun the same sealed fixture under the same inputs | Same packet/policy/gate outcome and a replay-verifiable receipt. |
| Remove the Pydantic/jsonschema boundary or replace a typed result with raw mapping | The real consumer holds/refuses; no raw-dict fallback. |
| Remove a selected solver/tool, change interpreter/provider/source digest, or alter a retained artifact | The consumer detects severance/drift before settlement. |
| Solver disagreement, `unknown`, missing model/witness/core, or finite-enumeration mismatch | `HOLD_DECIDER_DISAGREEMENT` or an equally precise hold. |
| Clone two member councils with the same roots | Provenance matrix labels correlation; multiplicity does not improve evidence count. |
| Falsifier returns a counterexample while other workers agree | Counterexample remains visible; controller holds or routes a bounded repair probe. |
| Receipt/SQLite tamper or retarget to a different valid run | Independent verifier refuses binding mismatch. |
| Provider timeout, cost ceiling, unavailable credential, or malformed response | No retry outside policy; result is retained as timeout/hold, not silently rerouted. |

Use Hypothesis against these *actual* transitions, not against an isolated
schema only.  Hypothesis is designed to generate edge cases across a stated
input range, so it is well suited to boundary, stateful, and replay properties
when its failure artifact is retained.  [Hypothesis documentation](https://hypothesis.readthedocs.io/en/latest/).

## What external research supports—and what it does not

| Source | Useful, bounded inference for CB | Invalid inference to avoid |
|---|---|---|
| [Anthropic: multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) | Parallel workers help breadth-first, decomposable research; specific objectives, output formats, tool boundaries, budgets, observability, retained artifacts, and small evals matter. | Multi-agent quantity, an LLM judge, or orchestration “best practice” creates deterministic authority.  Anthropic also reports high token cost and poor fit for tightly dependent work. |
| [Google DeepMind Co-Scientist](https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/) | Specialized generation, reflection, diversity, ranking, and meta-review are reasonable *exploration* roles to model as bounded probes. | Debate/ranking yields ground truth or can settle CB membership/promotion. |
| [Google DeepMind AlphaEvolve](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) | The useful loop is candidate → automated evaluation → retained evaluated artifact → later prompt selection.  Use cheap/broad and stronger/deeper model lanes only as controlled proposal sources. | A general evolutionary agent framework should be added before there is a concrete evaluator/consumer. |
| Pydantic, Z3, cvc5, Hypothesis primary docs above | Stronger typed envelopes, explicit solver outputs, retained diagnostics, and property-based mutation of real paths. | Schema validation or solver agreement proves the intended semantics without a correct, bounded encoding and independent replay. |

These are engineering analogies and test ideas, not scientific proof of an
“attractor,” a general swarm theory, or a replacement for owner law.  Describe
repeated outcomes as an **observed recurrence under a stated perturbation
matrix** until a specific dynamical claim has its own formal model and evidence.

## Tool posture for this phase

| Asset / class | First bounded use | Status to preserve now |
|---|---|---|
| `sqlite3` | Authoritative wave/receipt rows and replay identity. | Core mechanism; still needs each new consumer edge and portability evidence. |
| Pydantic + `jsonschema` | Strict envelopes and structural cross-check for IssueCard/ProbePacket/WorkerResult/Receipt. | Function-linked local boundary route only; not a 91-manifest member, portable adoption, gate solver, or provider framework. |
| Z3, cvc5, finite enumeration | Bounded decision/witness/counterexample checks. | Tools execute a declared encoding; they do not certify an unstated theory. |
| Rustworkx | Fixed-topology/DAG preflight. | Topology evidence only, not semantic evidence. |
| Hypothesis | Property/stateful falsification of actual gate and receipt transitions. | Candidate until a particular test suite/consumer is bound and exercised. |
| SymPy / Maude | Keep their existing narrowly defined formal roles if a fixture names a concrete consumer. | Do not make them bootstrap prerequisites solely because they exist in the estate. |
| PydanticAI | Evaluate only if a later real provider-worker adapter has a demonstrated seam that ordinary typed adapters cannot cover. | **Not an immediate dependency, scheduler, gate, or admission authority.** |
| Generic agent frameworks, queues, ORMs, simulation engines | Hold until a direct consumer, bounded API operation, severance test, and portability route exist. | Not implied by “nested council” or “wave.” |

PydanticAI may be useful later as a provider-adapter candidate, but its agent
graph/decision capabilities must never become a way for a model to select CB
policy or a terminal.  Admission must be earned by the same direct consumer,
negative/boundary/replay/severance, and portability evidence as every other
tool.

## Ordered implementation roadmap

### 1. Local fake-adapter fixture (next)

Implement one fixed, Light-only `WaveRecipe` around a current finite decision.
Use strict envelopes, SQLite state, fixed DAG preflight, local fake adapters,
and independent replay.  Start with the operation/witness, falsifier, and
evidence-mapper member councils.  Record all asset bindings as
`BOUND_REFERENCE` or `INVOKED` accurately.  No network provider, no new
framework, no Heavy import, and no claim of actual skill/MMM execution unless a
receipt proves it.

Exit criterion: positive, reason-specific negative, one-field boundary, replay,
severance, topology, provenance-correlation, timeout/budget, and receipt-tamper
tests all exercise the same controller route.

### 2. One actual skill/formal-adapter binding

Choose one existing, narrow procedure with a deterministic artifact contract
(for example, a formal solver check, a tooling falsification procedure, or a
specific skill that can produce a sealed receipt).  Bind it through
`ProbePacket -> WorkerResult`; keep the gate outside it.  Add an actual
invocation receipt that names the asset version/digest, MMM preload if any,
input roots, capabilities, output artifact, and verifier consumption.

Exit criterion: severing the adapter or changing its source/MMM/input digest
changes the real consumer outcome to HOLD/REFUSE; a described registry entry
alone cannot pass.

### 3. Optional provider-worker lane

Only after step 2, add a provider adapter to one role.  The adapter remains
untrusted and returns only a schema-validated `WorkerResult`.  Give it an exact
model/provider identity, time/token/cost ceiling, timeout behavior, prompt-card
digest, and restricted artifact set.  Use breadth-efficient calls for limited
independent probes and reserve stronger models for bounded ambiguity or
falsification audits—not because model rank confers authority.

Claude bridge, Haiku/Sonnet/Opus, Fable, and Luna Ultra are routes to evaluate
per explicit provider receipt and user-approved configuration.  They are not
currently interchangeable identities or integrated CB functionality merely
because they are available in a parent environment.  PydanticAI stays out
unless this adapter phase demonstrates a necessary, independently tested role.

Exit criterion: provider timeout, malformed packet, unexpected capability,
cost-boundary, duplicate roots, and model-route drift all fail closed before a
gate transition.

### 4. Evidence-gated nesting and management plane

Add a child council only where a parent has a proven non-LLM consumer, a
distinct finite subproblem, an explicit parent binding, novelty not explained
by shared roots, and remaining policy budget.  Implement management-plane
functions—receipt manager, laggard monitor, reroute manager, context loader—as
ordinary constrained adapters with their own receipts.  They cannot rewrite a
settled gate verdict.

Exit criterion: nested-run replay validates ancestry, budgets, provenance
matrix, child isolation, and non-overwrite of falsifier evidence.

### 5. Portable adoption evidence

Run fresh, isolated install/import/real-operation/replay/severance receipts on
macOS, Windows, and Linux for Python 3.12 and 3.13.  Bind a full transitive hash
closure and exact interpreter/provider origins.  A local wheel, an import, or a
CI matrix configuration is not an operating-system result.

Exit criterion: every claimed Light tool role has the required matrix cells or
is explicitly held.  Provider-backed routes additionally need their own
credential/network/timeout claim ceiling.

### 6. Later Heavy bridge, if needed

Only after the Light route is portable and a concrete workload needs it, define
a typed Light-to-Heavy bridge record with both-side profile IDs, interpreter
identity, setup/operation/replay receipts, and boundary refusal tests.  A
simulation engine is then a CB-managed workload target—not the source of
authority for the wave system.

## Claim ceiling after this research document

This document supplies a source-hierarchical, research-backed **plan** for a
CB Light-first nested-wave implementation.  It does not itself execute a wave,
run an LLM council, load an MMM, invoke a skill, admit PydanticAI, prove a
solver encoding, establish macOS/Windows/Linux portability, or advance CB
Heavy.  Each of those remains a separate receipt-bound transition.
