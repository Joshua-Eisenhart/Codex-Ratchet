# Parallel Sim Lanes

Claim a row by setting `owner` (your terminal id or `hermes-<n>`) and `status` to `in_progress`.
Use `scripts/claim_lane.py claim <lane_id> <owner>` for file-locked atomic claim.
Status values: `open`, `in_progress`, `runs`, `passes local rerun`, `canonical by process`, `blocked`.

Maintenance overlay:
- `M` rows are orthogonal to the build-stage lanes below
- keep one primary build lane plus one `M` row when controller work is active
- `M` never authorizes stage promotion

**Lane priority:** T (tool sims) and TI (tool integrations) stay active first; C (classical baselines) may run in parallel; NC (nonclassical lego stage) is the main completion surface; B (bounded coupling exploration) may run off strong NC parents; S (spine/bridge/axis closure) stays blocked.

Hard guardrail:
- do not interpret `NC` as "some local winners"
- do not interpret `B` as broad bridge/coupling permission
- `B` means bounded exploratory coupling off already-strong local parents
- `S` remains blocked until much later evidence exists

Classical-baseline sims (Lane C) must carry `classification: "classical_baseline"` and MUST NOT be cited as evidence for nonclassical claims.

## Lane T — Tool sims (isolation)

| id | tool | owner | status | result_path |
|---|---|---|---|---|
| T-01 | z3 |  | open |  |
| T-02 | cvc5 | | open | |
| T-03 | Cl(3) rotors | | open | |
| T-04 | Cl(6) rotors | | open | |
| T-05 | TopoNetX | | open | |
| T-06 | PyG message passing | | open | |
| T-07 | torch autograd | | open | |
| T-08 | sympy | | open | |

## Lane TI — Tool integration (pairwise first, then 3-stack)

| id | pair | owner | status | result_path |
|---|---|---|---|---|
| TI-01 | z3 × sympy | | open | |
| TI-02 | Cl(3) × PyG | | open | |
| TI-03 | TopoNetX × torch | hermes | blocked | system_v4/probes/a2_state/sim_results/system_hygiene_supervisor_results.json |
| TI-04 | z3 × torch | | open | |
| TI-05 | Cl(6) × TopoNetX | | open | |
| TI-06 | sympy × Cl(3) | | open | |

## Lane C — Classical baselines (scale-out; Hermes owns)

Populate from existing 713-probe inventory. Each row stays `classical_baseline`.

| id | sim | owner | status | result_path |
|---|---|---|---|---|
| C-01 | (seed from sim inventory) | | open | |

## Lane NC — Nonclassical geometry legos

Primary completion surface.
Keep running NC while T and TI continue to deepen.

## Lane B — Bounded coupling exploration

Allowed only off strong local parents.
Exploration only; not broad promotion.

## Lane S — Spine / bridge / axis closure

Blocked.

## Lane M — Maintenance / controller overlay

Non-admitting controller lane. Run beside the current primary build lane when truth, hygiene, contract, or worker/harness surfaces need repair.

| id | surface | owner | status | result_path |
|---|---|---|---|---|
| M-01 | truth / integrity verification | | blocked | system_v4/probes/a2_state/sim_results/probe_truth_audit_results.json |
| M-02 | hygiene / repository maintenance | | blocked | system_v4/probes/a2_state/sim_results/repo_hygiene_audit_results.json |
| M-03 | controller / harness contract governance | | blocked | system_v4/probes/a2_state/sim_results/controller_alignment_audit_results.json |
| M-04 | runtime / CLI worker prerequisites | | passes local rerun | system_v4/probes/a2_state/sim_results/runtime_hygiene_audit_results.json |
| M-05 | subagent + wiki harness integration |  | runs | system_v5/docs/plans/plans/subagent-wiki-harness-integration-contract.md |
