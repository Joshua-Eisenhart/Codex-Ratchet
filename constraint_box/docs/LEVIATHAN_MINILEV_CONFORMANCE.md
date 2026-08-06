# Leviathan reference → CB Mini-Lev conformance

ConstraintBox does not package Leviathan, FlowMind, a provider adapter, or a
general agent runner.  Its Mini-Lev is a small Python kernel that keeps the
useful deterministic parts: frozen policy, bounded graph, typed hooks,
controller-selected transition, receipt/ledger replay, and a controller-owned
execution lease.

The first reference is Lev's `plugins/sdlc/flows/exec-validate.flow.yaml`.
CB observes its exact named source shape rather than accepting arbitrary Lev
YAML. Lev's `validate` node is still `op: lev.exec`; it is not a deterministic
gate and CB does not inherit its authority.

```text
Lev: exec -> validate --pass--> emit -> done
                     --fail--> exec (bounded retries)
                     --timeout--> escalate -> done

CB:  execute tool -> validate gate --PASS--> emit tool -> seal gate -> ELIGIBLE
                                  --RETRY--> execute tool (max 2)
                                  --exhausted--> HOLD
```

`HOLD` is intentional.  It is safer than copying Lev's escalation node because
CB must not let a timeout invoke an LLM, provider, or user-authority action.
An advisory interface may explain the held receipt later, but it cannot choose
the transition.

## What is measured

`constraintbox.leviathan_reference.run_reference_conformance()` runs two
CB-native, fully replayed flows:

| Scenario | Required result |
|---|---|
| one retry, then valid gate result | `ELIGIBLE`; tool, gate, emit, and seal gate all completed |
| retries beyond the controller budget | `HOLD`; exactly two persisted retries; no positive terminal |

The optional external adapter runs the real Lev CLI with `--dry-run` under a
fresh XDG root. It validates the narrow `lev.run_seal.v1` semantic subset:
source intent reference, admitted sealed run, dry-run receipt/trace evidence,
no proof-backed execution, and no passing execution claim. It then checks the
observed Lev graph against the CB graph: two-phase order, bounded retry loop,
pass path through emit, the intentional timeout-to-`HOLD` difference, and the
fact that CB imports no Lev gate authority. It also mutates the observed seal
in memory to prove a real-execution outcome or proof-bearing/passing receipt
is rejected.

```bash
PYTHONPATH=src python -m constraintbox.leviathan_reference \
  --lev-root /path/to/lev-main \
  --subject-root /path/to/constraint_box \
  --run-root /absolute/new/run-root \
  --request-id lev-reference-1 \
  --output /absolute/new/lev-reference-result.json
```

The external adapter is `EXTERNAL_NOT_CB_KERNEL`.  A passed dry run proves only
that one local Lev control-plane shape and one CB Mini-Lev flow were observed.
It does not prove full Lev parity, provider availability, an LLM run, agent
authorization, release, promotion, or scientific/CR content.

## Extraction ledger

The ledger separates a useful control-plane mechanism from the authority that
happens to implement it in Lev. “Retain” means CB owns a small Python form of
the mechanism; it does not mean that CB imports Lev code or accepts Lev output
as a verdict.

| Lev concept | CB treatment | Current CB state | Ceiling |
|---|---|---|---|
| content-addressed intent reference | retain as a typed request/context/receipt digest binding | active Mini-Lev receipt binding | identity and replay evidence, not truth |
| two-phase `exec -> validate` order | retain the ordering, replace validation with a deterministic code `GATE` | active reference flow | Lev `validate` itself remains `lev.exec`, never a CB gate |
| bounded `fail -> exec` retry | retain as `RETRY -> execute` with a frozen numeric budget | active, max two retries in the reference flow | no error-class heuristic or model-selected retry |
| terminal lifecycle reducer | retain a hash-chained event stream reduced to one terminal | active Mini-Lev replay | local tamper evidence, not external signature |
| receipt/evidence references | retain independent receipt and retained-head verification | active | receipt presence never creates a pass |
| positive terminal after validation | retain and strengthen: a CB `GATE PASS` plus all required nodes must complete | active | no general truth or release claim |
| dry-run versus proof-backed execution | retain as an external-reference boundary | active in the Lev adapter | a dry-run is not a real execution result |
| attempt/visit accounting | retain bounded retry and per-node visit counters in the receipt | active | no throughput or performance claim |
| FlowMind graph shape | retain only fixed controller-authored graph mechanics through Rustworkx | active; one Lev source shape is observed | no user/model-authored YAML admission |
| lease type | retain only controller-owned holder, scope, expiry, release, and replay | first fixed-hook binding exists | no model-issued lease, distributed lease, or release authority |
| repeated-intent/idempotency collapse | park as a future explicit conformance property | not claimed | no cross-run equivalence claim yet |

## Rejection ledger

| Lev surface | CB disposition | Why it stays outside the kernel |
|---|---|---|
| `lev.exec` as a node operation | reject as gate/transition authority | it selects adapters, model profiles, and effects outside a deterministic CB gate |
| model-authored `task`, `until`, or `done_criteria` | reject as control input | generated text must not decide flow completion or successor node |
| `validate` model report of `PASS`/`FAIL` | reject as a gate verdict | CB validates bounded evidence with code, SMT-aligned checks, and receipt replay |
| escalation prompt / AgentPing route | replace with `HOLD` | exhaustion cannot turn into a model or human authority action inside the flow |
| provider routing, Poly catalogs, model profiles | external/advisory only | they are configuration and execution surfaces, not proof instruments |
| evaluator/sensor-scored verdicts | reject from the decision path | a scored or heuristic measurement cannot choose a CB disposition |
| error-class retry, backoff, or jitter policy | reject from the reference flow | CB retries only on a typed deterministic gate signal under a fixed count |
| Lev admission state or decision references | observe only | a foreign decision cannot be promoted into a CB decision |
| heuristic memory extraction | do not import | MMM is a separate, versioned semantic-compression input contract |

MMM use is intentionally straightforward: a controller-selected, schema-bound
profile is injected as bounded input with provenance and a digest; it may help
an advisory model phrase a response, but cannot select a tool, gate, retry,
lease, release, or terminal. The meaningful Mini-Lev work is the deterministic
control loop around that input.

This is a bounded structural conformance and extraction harness, not a claim
that Mini-Lev has become a copy of Leviathan. It has no repeated-intent
idempotency equivalence claim yet.
