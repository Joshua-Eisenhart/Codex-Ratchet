# Mini-LevOS and Wave-Model Clarity Audit

Status: source-bound working understanding; noncanonical; 2026-08-10.

This document turns the two supplied owner-prompt pastes into one contained
working model.  It does **not** promote pasted browser answers, historical
reports, or copied status claims into runtime truth.  Current source, focused
tests, and retained receipts remain the evidence for implemented behavior.

## The clarified model

ConstraintBox has two linked but non-conflated parts:

```text
CB Light: portable, mostly-Python deterministic control plane
  typed packet -> deterministic gate -> Mini-Lev settlement -> receipt
                    ^
                    | bounded waves of LLM/tool probes explore evidence

CB Heavy: CB-managed simulation estate
  separately profiled environment -> setup/operation/replay receipt
                    ^
                    | a Light wave may target it, but does not need it to run
```

CB Heavy is part of ConstraintBox because CB installs, maintains, integrates,
runs, and audits it.  It is nevertheless outside CB Light's runtime identity
and may not silently supply Light authority, an interpreter, a package
membership decision, or a completion claim.

A wave is not the whole tool stack.  It is a finite, persisted management
process for a bounded swarm of probes around a deterministic gate.  Tools also
belong directly in gates, installation/maintenance, evidence verification, or
Heavy bridges.  A single tool can have more than one role, but each role needs
its own caller, inputs, constraints, and receipt.

## Direct owner intent preserved from the pastes

1. The whole repo estate remains a **mechanism mine**, not a package import
   list.  ClaimGate's LevOS-patch history is useful because it exposes
   extractable mechanisms; it is not an authority to import wholesale.
2. CB Light must be genuinely portable across macOS, Windows, and Linux.
   Local installation or a pure-Python wheel does not establish that state.
3. LLMs, skills, formal agents, CB Light tools, and MMMs can all participate as
   nested council members or supports.  They generate or examine probe
   artifacts; none obtains deterministic gate authority from that role.
4. Nested waves create breadth and controlled convergence, but a majority or
   a model synthesis is never the truth condition.  Counterexamples, replay,
   and a deterministic controller settle a transition.
5. Cheap model lanes may cover breadth; stronger models may audit difficult
   conflicts.  Model tier is separate from authority and claim ceiling.

## What the live Mini-LevOS kernel already brings

The active package contains `constraintbox.mini_levos`, not an imported LevOS
runtime.  Its useful retained mechanisms are:

| Mechanism | Current bounded behavior | Correct future CB use |
|---|---|---|
| Frozen `FlowPolicy`, nodes, and transitions | Controller fixes the graph before a run. | Declare a wave settlement graph; never accept a model-authored graph. |
| Typed hook registrations/results | Hook output, allowed signals, update keys, and byte bounds are checked. | Give probe adapters a narrow `ProbePacket -> WorkerResult` boundary. |
| Controller-owned transition reducer | A hook can report a signal but cannot select an unauthorized successor. | Let the controller settle `SETTLED`, `HOLD`, `REFUSE`, or `EXPIRED`. |
| Budgets | Step, visit, retry, context, event, and receipt bounds are enforced. | Put depth, children, cost, time, artifacts, and retries in policy, not prompts. |
| Hash-chain ledger and receipt replay | Events are retained and a receipt is verified against the retained head. | Preserve positive and negative probe artifacts, not only a final summary. |
| Runtime identity checks | Runtime/hook identity drift converts work to a hold. | Bind the exact interpreter and provider/tool identity to a wave receipt. |
| Controller-owned execution lease | A selected hook can be held inside a scoped lifecycle with audited release. | Use for a bounded external operation only; never issue a lease from model text. |
| Topology preflight | A fixed topology may be evaluated before execution. | Reject cycles, illegal ancestry, and child-before-parent settlement. |
| Provider/notary boundary | A provider supplies proposal bytes; controller policy, gate, and receipt own the route. | Treat LLM output as an untrusted candidate artifact. |

There is executable evidence for this kernel: the current focused
Mini-LevOS, execution-lease, and contained-provider test invocation completed
successfully under the contained CB environment.  A retained proposal-flow
receipt also shows a four-step Mini-Lev run with all four required nodes
completed, while explicitly retaining `promotion_allowed: false`.  That is
evidence for a bounded local proposal flow, not for portable Light, universal
hooks, a general council runtime, CB Heavy readiness, or release.

## What Mini-LevOS must not import or become

- No external Lev/ClaimGate decision may become a CB verdict merely because it
  is present or has a receipt.
- No arbitrary FlowMind/YAML, user prompt, MMM, or model output may define a
  flow, successor, retry budget, lease, provider route, or terminal.
- No scored model consensus, ranking, or Bayesian-looking confidence becomes
  an admission decision without a deterministic evidence predicate.
- No generic agent framework is required for the first wave.  Existing
  Rustworkx, SQLite, the Mini-Lev policy/runtime, and strict typed packets are
  sufficient for a small deterministic starting loop.
- No Heavy environment, engine receipt, or simulation dependency crosses into
  Light by import-path accident.

## Terms that must stay distinct

| Term | Meaning in this model | Not equivalent to |
|---|---|---|
| Probe | One bounded test or evidence-seeking operation, including required negative cases. | A linear agent task or a vote. |
| Gate | Deterministic code/tool decision over bounded inputs and evidence. | A model review or a collection of green imports. |
| Wave | Persisted batch of independently bounded probes around one issue/gate. | The whole CB runtime or every tool in CB. |
| Council | A role-structured collection of members within a wave; nesting is optional and evidence-gated. | A truth-producing parliament. |
| MMM | Versioned, provenance-bound saliency/vocabulary input. | Policy, authority, mutable global memory, or a gate. |
| Mini-LevOS | CB-owned finite flow/ledger/lease mechanism extracted in small form. | LevOS/ClaimGate wholesale integration. |
| CB Heavy | CB-managed simulation estate with separately earned profiles. | A prerequisite for Light waves. |

## Reconciliation of material conflicts

The supplied material contains several useful but incompatible status claims.
They should not be smoothed into one green narrative.

| Topic | Working treatment |
|---|---|
| `91 installed/86 selected` reports versus current manifest | Retain past reports as local-install/selection leads only.  The current Light manifest is proposal-only and the present contained Pydantic route has a smaller, independently verified claim ceiling. |
| “Hooks are fully live” | Treat as configuration/manual-test evidence until the normal hook route, alternate route, and SQLite authority are demonstrably the same transition. |
| `constraintbox run` documentation versus current console | The public Mini-Lev proposal path is reachable through installed `constraintbox-legacy run`; the default `constraintbox` console exposes only `doctor`, `exercise`, `gate`, and `control-plane`.  This is a packaging/documentation seam to reconcile before calling Mini-Lev the normal Light hook spine. |
| Browser-listed Codex hook APIs and third-party repositories | Candidate research only.  Do not adopt event names, hook payload schemas, package claims, or project templates without current primary-source and local compatibility verification. |
| Broad multi-agent/framework recommendations | Candidate mechanisms, not a dependency mandate.  Frameworks such as LangGraph, PydanticAI, Instructor, CPMpy, Scallop, and PyReason need a real role, portable install evidence, and a consumer before admission. |

## First coherent wave experiment

The next wave should be a **Light-only** local experiment, no network provider
and no Heavy engine:

```text
sealed IssueCard
  -> strict ProbePacket validation
  -> three independent probes
       1. operation/witness probe
       2. counterexample/falsifier probe
       3. evidence-map/provenance probe
  -> Rustworkx topology preflight + deterministic finite gate
  -> Mini-Lev settlement and hash-chain receipt
  -> SQLite projection + read-only replay verifier
  -> SETTLED | HOLD | REFUSE | EXPIRED
```

Each probe must have a positive, a reason-specific negative, a one-field
boundary mutation, replay, severance, cost/time ceiling, and a retained
artifact.  The falsifier has a protected right to retain a counterexample;
later model agreement cannot overwrite it.

Only add a child council when a parent already has a non-LLM consumer, a
distinct finite subproblem, unspent policy budget, an explicit parent ID, and
measured novelty.  “Attractor basin” remains a hypothesis until controlled
perturbation runs show the same verified settlement and preserve divergent
results.

## Immediate work order

1. Preserve and index mined CB/ClaimGate/Mini-LevOS mechanisms as candidate
   mechanisms, rather than importing another framework or rebuilding a gate
   that already exists.
2. Establish one clean, contained CB Light tool environment.  For every
   candidate, record the exact interpreter, distribution/version/provider,
   pin/closure, import origin, `pip check`, and a real API operation.
3. Apply the tool constraints to each *role binding*, not merely each package:
   positive, reason-specific negative, one-field boundary, replay, severance,
   source/consumer hash, and later the three-OS/two-Python matrix.
4. Bind the first accepted tool roles into the existing deterministic gate and
   Mini-Lev transition; then make the public CLI, hook route, and alternate
   route consume the same selection/receipt authority.
5. Use premortem, loophole-audit, and portability skills now as bounded
   falsification assistance for steps 2–4.  Their outputs can expose missing
   constraints but cannot promote a tool or settle a gate.
6. Only after step 4, define `IssueCard`, `ProbePacket`, `WorkerResult`, and
   `WaveReceipt`, then run the Light-only fake/local three-probe experiment.
7. Admit more tool roles, model lanes, nesting, and Heavy bridges only through
   separate receipt-bound transitions.

This preserves the full architectural idea—probes, waves, councils, MMMs,
formal tools, and a CB-managed Heavy estate—without letting any one document,
framework, model, or historical implementation collapse those boundaries.
