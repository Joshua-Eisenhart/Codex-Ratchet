# Tool-Stage Routing and Skip-Ahead Contract

Date: 2026-04-19
Status: binding process document for the tool stage
Authority: accepts Codex correction 2026-04-19 that recent default-queue drain was real work routed through the wrong surface

## Why this file exists

The controller previously treated `queue_default.txt` as a general drain surface and used successful DONE counts as a proxy for tool-stage progress. That conflated five distinct things:

1. Smoke test — does the tool import and run a minimal example.
2. Capability probe — does the tool produce the invariants claimed of it.
3. Integration probe — do two tools crosscheck on a scoped question.
4. Tool-serving real-lego test (skip-ahead) — a bounded row answering one tool-integration question against a real lego, with mandatory loopback to the ledger.
5. Full sim (classical baseline, canonical, or gray-zone) — downstream consumer of tool-stage closure, not part of it.

Those are five different stages, in that order, recursive. A pass at one stage does not discharge debt at another. A generic lego drain is not a tool-stage advance.

## Routing rule

| Row type | Queue surface | Loopback required? |
|---|---|---|
| Stage 1–3 (smoke / capability / integration) | `queue_tier_a.txt` | Yes — to `TOOL_CAPABILITY_AND_INTEGRATION_LEDGER.md` |
| Stage 4 (tool-serving real-lego skip-ahead) | `queue_tier_a.txt` with BOUND block | Yes — to `loopback_target` declared in the BOUND block |
| Stage 5 full sim, bounded lego work | `queue_tier_b.txt` (shell-local) or `queue_tier_d.txt` | No — but must carry classification field in probe |
| Classical baselines, FEP/holodeck/leviathan locals, axis-composites | `queue_lego_backlog.txt` (tracked holding surface; not default-drained) | No |
| Bridge composites, multi-shell stacks, off-lane | `queue_offlane.txt` (never auto-drained) | No |
| Utility, telemetry, calibration | `queue_disposal.txt` or script direct | No |

Default-queue rows that fall into stages 1–4 are routing failures. They must be rerouted to `queue_tier_a.txt` with their ledger loopback declared explicitly, not re-run.

## Tool role-discovery axis

Every tool in the ledger gets a discovered role, recorded in a new column:

- `nonclassical-core` — essential to a nonclassical admissibility proof.
- `nonclassical-support` — load-bearing in nonclassical-admissible sims but replaceable.
- `bridge-useful` — classical machinery whose output feeds nonclassical sims (Carnot / Szilard / FEP / persistence baselines).
- `classical-only` — load-bearing only in classical baselines.
- `controller-support` — runs controller or telemetry; not itself sim-stage.

Role is discovered by probing, not declared. A probe that tries a tool for nonclassical work and finds it unsuitable moves the tool to `classical-only` with the failing probe cited. The ledger currently conflates load-bearing-anywhere with nonclassical-suitable; that conflation is the next honest ledger debt.

## Skip-ahead admissibility contract

Any row entering stage 4 (tool-serving real-lego test) must carry an eight-field BOUND block immediately preceding its queue line:

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

1. BOUND block required on stage-4 rows. Missing → INELIGIBLE.
2. Any BOUND field empty or absent → INELIGIBLE.
3. `expected_outcome_classification: canonical` with no nonclassical-suitable load-bearing tool → INELIGIBLE.
4. On DONE, verify the file at `loopback_target` was touched since run-start and contains the named row. If not → LOOPBACK_MISSING, reroute to `queue_disposal.txt`.
5. Probe output JSON that claims a field listed in `out_of_scope` → SCOPE_VIOLATION, reroute to `queue_disposal.txt`.

INELIGIBLE is a routing fault, not a runtime failure. It does not trip the consecutive-failure circuit-breaker. It re-routes the row off the tier-A surface.

## What this file explicitly does NOT do

- It does not retro-delete the 511 default-queue DONEs. They are reclassifiable, not garbage.
- It does not authorize lego-stage skipping. Stage 4 is tight and scoped; it answers one tool question per row.
- It does not unify the wiki harness tool probes with repo sim-tool substrate probes. Those remain distinct.
- It does not promote any current tool to nonclassical-core without a probe. The role-discovery axis is populated only by evidence.

## Open debts after this file lands

- Role-discovery column not yet added to `TOOL_CAPABILITY_AND_INTEGRATION_LEDGER.md` — schema change, owner review needed.
- Runner (`sim_runner.sh`) does not yet enforce the admission gate. The v2 stub at `system_v5/ops/drafts/sim_runner_v2_stub.sh` sketches the intended gate, is not live, and is not executable.
- `queue_lego_backlog.txt` and `queue_offlane.txt` now exist as explicit partition surfaces. They are holding areas, not proof that the rows inside them are admitted or safe to auto-drain.
- Reclassification of the 511 default-queue DONEs into the seven buckets (tool-serving / nonclassical-support / classical-support / bridge-useful / generic-lego-backlog / off-lane / runtime-residue) is a separate pass, not done here.

## Authority

This file binds when the controller is operating against the tool stage. It is subordinate to `ENFORCEMENT_AND_PROCESS_RULES.md` and `LLM_CONTROLLER_CONTRACT.md`. Where this file and those documents disagree, those documents win.
