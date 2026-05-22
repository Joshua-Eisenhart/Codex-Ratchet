# Tool-Stage Routing and Skip-Ahead Contract

Date: 2026-04-19
Status: binding process document for the tool stage
Authority: accepts Codex correction 2026-04-19 that recent default-queue drain was real work routed through the wrong surface

## Why this file exists

The controller previously treated `queue_default.txt` as a general drain surface and used successful DONE counts as a proxy for tool-stage progress. That conflated six distinct things:

1. Smoke test — does the tool import and run a minimal example.
2. Function/API micro-probe — does one named tool function or API surface produce the invariant claimed of it.
3. Tool-lego fit probe — can that one tool function carry a useful bounded lego-shaped question.
4. Tool-tool coupling probe — do two individually receipt-validated tool functions exchange output/input or cross-check one scoped question.
5. Tool-serving real-lego test (skip-ahead) — a bounded row answering one tool-integration question against a real lego, with mandatory loopback to the ledger.
6. Full sim (classical baseline, canonical, or gray-zone) — downstream consumer of tool-stage closure, not part of it.

Those are different stages, in that order, recursive. A pass at one stage does not discharge debt at another. A generic lego drain is not a tool-stage advance.

`DONE` means the runner executed a queued row. It is not controller admission, not ledger reconciliation, and not coupling readiness until the queue row, result JSON, `classification`, tool-integration depth, and loopback target all agree.

## Micro-stage ladder

Tool-stage work moves in tiny steps:

1. pick one tool;
2. pick one function/API surface from that tool;
3. pick the smallest claim that function should certify, compute, exclude, or transform;
4. pick one useful lego target or minimal fixture that exposes the claim;
5. write positive, negative, and boundary tests;
6. record the failure condition that would demote the tool role;
7. update the ledger with the exact evidence path.

This is pre-lego work even when it uses a real lego-shaped target. It receipt-validates the tool/function surface for one bounded claim, not the lego, not the stack, and not a downstream coupling. Workers may run many independent micro-probes in parallel, and multiple workers may test the same triple in different ways, but each accepted row must keep only one thing uncertain.

Do not debug stacked uncertainty. If a packet requires debugging the tool, the lego object, and another tool coupling at the same time, split it.

## Sim-mode parallelization rule

Independent tool/function surfaces can be worked in parallel. The default fanout surface is packet authoring, MICRO/BOUND block drafting, manifest checking, ledger-loopback planning, and audit/review for separate tools, function surfaces, or rows.

Runner execution remains serial only where the runner requires it: shared queue mutation, shared result paths, fixture contention, prior-receipt dependency, stage-gate dependency, or a runner implementation that is not concurrency-safe. Do not treat runner serialization as a reason to serialize independent LLM/tool packet preparation or audit work.

Acceptance remains row-local: each accepted packet must name one tool/function surface, one tiny claim, its own evidence path, and its own ledger loopback. Parallel work must not merge uncertain tool behavior, lego behavior, and coupling behavior into one packet.

The stage gate is conservative by design, so the search before it should be
wide. Workers may produce many MICRO/BOUND candidates, alternate lego targets,
negative cases, and demotion probes. A failed candidate that cleanly identifies
the missing function receipt, bad tool role, over-broad lego claim, or coupling
debt is useful ratchet evidence. It should be recorded, split, demoted, or
rerouted; it should not be promoted.

## Child/subsubagent status ceiling

Subagents and subsubagents can improve packet quality by testing alternate
model/reasoning salience, finding missing prior receipts, drafting stricter
MICRO/BOUND fields, or falsifying a proposed queue row. They cannot make a row
queue-ready by agreement. A child receipt that says "promising," "council
agreed," "runner passed," or "ready" remains advisory until the controller
reads the exact artifact and the relevant compile gate passes.

For Stage 3 and Stage 4, child receipts may produce a `queue_candidate` only.
Queue visibility still requires the strict fields, stage gate, exact
tool/function or admitted coupling, positive check, negative/boundary check,
expected result path, prior receipts when required, and explicit blocked or
admission status. Missing pieces must return `split_smaller` or `blocked`, not
an inferred promotion.

## Routing rule

| Row type | Queue surface | Loopback required? |
|---|---|---|
| Stage 1-2 (smoke / function micro-probe) | `queue_tier_a.txt` | Yes — to `TOOL_CAPABILITY_AND_INTEGRATION_LEDGER.md` |
| Stage 3 (tool-lego fit probe) | `queue_tier_a.txt` with micro packet fields | Yes — to the named tool/function ledger row |
| Stage 4 (tool-tool coupling probe) | `queue_tier_a.txt` with both prior receipts named | Yes — to both tool/function rows and the integration row |
| Stage 5 (tool-serving real-lego skip-ahead) | `queue_tier_a.txt` with BOUND block | Yes — to `loopback_target` declared in the BOUND block |
| Stage 6 full sim, bounded lego work | `queue_tier_b.txt` (shell-local) or `queue_tier_d.txt` only when `stage_gate.json` permits Tier D | No — but must carry classification field in probe |
| Classical baselines, FEP/holodeck/leviathan locals, axis-composites | `queue_lego_backlog.txt` (tracked holding surface; not default-drained) | No |
| Bridge composites, multi-shell stacks, off-lane | `queue_offlane.txt` (never auto-drained) | No |
| Utility, telemetry, calibration | `queue_disposal.txt` or script direct | No |

Default-queue rows that fall into stages 1–4 are routing failures. They must be rerouted to `queue_tier_a.txt` with their ledger loopback declared explicitly, not re-run.

## Tool role-discovery axis

Every tool in the ledger gets a discovered role, recorded in a new column:

- `nonclassical-core` — essential to a nonclassical admissibility proof.
- `nonclassical-support` — load-bearing in nonclassical-admissible sims but replaceable.
- `bridge-useful` — classical-side output that a later bridge sim may consume; not bridge evidence and not nonclassical support by itself.
- `classical-only` — load-bearing only in classical baselines.
- `controller-support` — runs controller or telemetry; not itself sim-stage.

Role is discovered by probing, not declared. A probe that tries a tool for nonclassical work and finds it unsuitable moves the tool to `classical-only` with the failing probe cited. The ledger currently conflates load-bearing-anywhere with nonclassical-suitable; that conflation is the next honest ledger debt.

Failed role-discovery probes are evidence when they cite the exact function
surface, claim ceiling, and demotion condition. They do not promote the tool,
but they prevent the next packet from pretending the role is still unknown.

## Sim execution-kind axis

The runner has three execution kinds. These are runner/admission labels, not replacements for result `classification`.

| Sim execution kind | What it is | Runner/tool rule |
|---|---|---|
| `classical` | Baselines, controls, and negative/reference comparisons | May use classical-only or bridge-useful tools, but load-bearing use does not make the result nonclassical. Preserve `divergence_log` when classified `classical_baseline`. |
| `nonclassical` | Canonical nonclassical-target sims | Use claim-relevant nonclassical tools: PyTorch/PyG for tensor or graph dynamics, Clifford for geometric product/spinor/rotor claims, and z3/cvc5 for structural proof or UNSAT claims. Missing relevant surfaces must be blocked/deferred, not silently ignored. |
| `bridge` | Explicit seam work between classical baselines and nonclassical structure: `bridge`, `Xi`, `rho_AB`, `Phi0`, cut/kernel, engine, or named pairwise/coupling/coexistence bridge rows | Requires both a named classical-side source and a nonclassical target/tool plan. Pairwise, coupling, coexistence, and engine rows stay exploratory unless both sides are named. Default and lego-backlog runners do not auto-drain it. |

`classification` says what status the result currently claims. `sim_execution_kind` / `runner_class` says which runner/tool admission law must apply before execution.

## Skip-ahead admissibility contract

Any row entering stage 3 or 4 should carry these micro packet fields in its plan, prompt, or queue preface:

```
# MICRO: {
#   "tool_target": "<tool name from the ledger>",
#   "function_surface": "<exact function/API surface being tested>",
#   "micro_claim": "<one tiny claim>",
#   "lego_target": "<bounded lego target or minimal fixture>",
#   "claim_ceiling": "<highest admissible claim, e.g. tool_function_micro_only or tool_integration_micro_only>",
#   "next_lego_target": "<named lego row/fixture this may unlock, or none>",
#   "promotion_condition": "<exact evidence required before any lego/coupling use>",
#   "blocked_until": "<what remains missing before promotion>",
#   "function_receipt": "<existing receipt for this function, or 'new' for a first receipt>",
#   "prior_function_receipts": ["<required before tool-tool coupling; empty for first proof>"],
#   "why_this_lego": "<why this target exposes the function>",
#   "positive_case": "<what must pass>",
#   "negative_case": "<what must fail>",
#   "boundary_case": "<edge condition>",
#   "demotion_condition": "<what would show the tool/function is not suitable here>",
#   "out_of_scope": ["<anything this row must not claim>"]
# }
```

Any row entering stage 5 (tool-serving real-lego test) must carry an eight-field BOUND block immediately preceding its queue line:

```
# BOUND: {
#   "tool_target": "<tool name from the ledger>",
#   "integration_question": "<the specific question this row answers, one sentence>",
#   "anchor_lego": "<lego registry id, e.g. L12_hopf_torus>",
#   "why_this_lego": "<why this lego exercises this tool-question, one sentence>",
#   "loopback_target": "<ledger row name that MUST be updated on DONE>",
#   "expected_outcome_classification": "classical_baseline | canonical | gray_zone",
#   "bound_exit_condition": "<what marks this row as answering the question>",
#   "out_of_scope": ["<list of things this row must not claim>"]
# }
```

## Admission gate

The runner (next version) enforces:

1. MICRO fields required on stage-3 and stage-4 rows. Missing → INELIGIBLE. Strict run-boundary reconciliation also requires `claim_ceiling`, `next_lego_target`, `promotion_condition`, and `blocked_until`.
2. BOUND block required on stage-5 rows. Missing → INELIGIBLE.
3. Any required MICRO or BOUND field empty or absent → INELIGIBLE.
4. A stage-3 first proof may set `function_receipt: "new"`, but it must still name the exact function surface, lego target, positive/negative/boundary cases, and demotion condition.
5. A tool-tool coupling with no prior receipt for both named function surfaces → INELIGIBLE.
6. A stack or compound row that fails while any participating tool function lacks an individual receipt → DECOMPOSE, not retry. Move back to the first missing micro proof.
7. `expected_outcome_classification: canonical` with no nonclassical-suitable load-bearing tool → INELIGIBLE.
8. On DONE, verify the file at `loopback_target` was touched since run-start and contains the named row. If not → LOOPBACK_MISSING, reroute to `queue_disposal.txt`.
9. Probe output JSON that claims a field listed in `out_of_scope` → SCOPE_VIOLATION, reroute to `queue_disposal.txt`.
10. Ledger-only repair rows must use `LEDGER_DONE`, not `DONE`. They may reconcile ledger text, but they are excluded from default executable reconciliation and still fail executable run-boundary admission when explicitly included.
11. Bridge, axis, engine, emergence, Tier D, or scientific-coupling language in the positive claim surface fails while `stage_gate.json` blocks that claim. Coupling language requires exact executable parent receipts.

After DONE, admission remains provisional until the controller reconciles the queue row, result path, result `classification`, `TOOL_INTEGRATION_DEPTH`, and ledger loopback. DONE counts must not be used to infer that a coupling has both parent functions ready.

INELIGIBLE is a routing fault, not a runtime failure. It does not trip the consecutive-failure circuit-breaker. It re-routes the row off the tier-A surface.

## What this file explicitly does NOT do

- It does not retro-delete the 511 default-queue DONEs. They are reclassifiable, not garbage.
- It does not authorize lego-stage skipping. Stage 3 uses lego-shaped targets to test tools; Stage 5 is tight and scoped; each row answers one tool question only.
- It does not unify the wiki harness tool probes with repo sim-tool substrate probes. Those remain distinct.
- It does not promote any current tool to nonclassical-core without a probe. The role-discovery axis is populated only by evidence.

## Open debts after this file lands

- Role-discovery column not yet added to `TOOL_CAPABILITY_AND_INTEGRATION_LEDGER.md` — schema change, owner review needed.
- Runner (`sim_runner.sh`) now honors the coarse stage gate for Tier D and default-queue late-stage blocking, but it does not yet enforce the full MICRO or BOUND admission gate. The v2 stub at `system_v5/ops/drafts/sim_runner_v2_stub.sh` sketches the intended BOUND gate, is not live, and is not executable.
- `queue_lego_backlog.txt` and `queue_offlane.txt` now exist as explicit partition surfaces. They are holding areas, not proof that the rows inside them are admitted or safe to auto-drain.
- Reclassification of the 511 default-queue DONEs into the seven buckets (tool-serving / nonclassical-support / classical-support / bridge-useful / generic-lego-backlog / off-lane / runtime-residue) is a separate pass, not done here.

## Authority

This file binds when the controller is operating against the tool stage. It is subordinate to `ENFORCEMENT_AND_PROCESS_RULES.md` and `LLM_CONTROLLER_CONTRACT.md`. Where this file and those documents disagree, those documents win.
