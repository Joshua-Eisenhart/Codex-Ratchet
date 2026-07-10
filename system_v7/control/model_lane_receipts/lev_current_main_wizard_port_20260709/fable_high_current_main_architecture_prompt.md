You are an independent architecture and false-green auditor. Read the live clean worktree at:

`/Users/joshuaeisenhart/.config/superpowers/worktrees/lev/current-main-wizard-port-20260709`

This worktree tracks current `origin/main`. An older Lev branch contains a receipt-bound multi-model Wizard and direct provider lanes, but current main has deleted that legacy subtree and has a substantially different execution architecture. Do not assume the old placement is valid.

Audit current main deeply enough to answer:

1. What exact current contracts should a receipt-bound three-council or multi-model Wizard reuse? Cite files and symbols in `core/domain`, `core/exec`, `core/eval`, `core/poly`, `core/flowmind`, and `plugins/samurai` where relevant.
2. Where may provider SDK/API implementations live, and where are they explicitly forbidden by boundary tests?
3. Define the smallest honest vertical slice that invokes one real model, binds the requested and resolved model, captures raw output plus timing/token/cost provenance, projects measurements without importing verdicts, and produces a replayable proof/eval bundle.
4. Which parts of the old Wizard idea remain domain semantics, which belong in FlowMind/plugin composition, and which should not be ported?
5. Audit the current-main baseline. `core/event-providers` and `core/eval` typecheck after install, while `core/exec` initially reports unresolved `@lev-os/flowmind/exec-flow-validation` and `@lev-os/config/source-catalog` declarations. Determine whether this is an install/build-order issue, lockfile drift, or code defect. Do not fix it.
6. Give an explicit no-go list and an evidence-calibrated recommendation: port now, first make a bounded POC, or hold.

Rules:

- Read-only. Do not edit any file.
- Treat model prose as advisory evidence, never a verdict.
- Separate invocation truth, measurement, gate decision, and proof bundle.
- Reject any path that would recreate provider implementation inside forbidden core ownership.
- Cite exact paths and line numbers.
- State uncertainties and baseline limitations.

Return a concise but technically complete audit with a recommended first implementation slice and tests.
