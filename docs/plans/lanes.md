# Parallel Sim Lanes

Claim a row by setting `owner` (your terminal id or `hermes-<n>`) and `status` to `in_progress`.
Use `scripts/claim_lane.py claim <lane_id>` for file-locked atomic claim.
Status values: `open`, `in_progress`, `runs`, `passes local rerun`, `canonical by process`, `blocked`.

**Lane priority:** T (tool sims) > TI (integration) > C (classical baselines, scale-out) > NC (nonclassical, blocked on T+TI) > B (bridge) > S (spine, blocked on NC).

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
| TI-03 | TopoNetX × torch | | open | |
| TI-04 | z3 × torch | | open | |
| TI-05 | Cl(6) × TopoNetX | | open | |
| TI-06 | sympy × Cl(3) | | open | |

## Lane C — Classical baselines (scale-out; Hermes owns)

Populate from existing 713-probe inventory. Each row stays `classical_baseline`.

| id | sim | owner | status | result_path |
|---|---|---|---|---|
| C-01 | (seed from sim inventory) | | open | |

## Lane NC — Nonclassical geometry legos (BLOCKED on T+TI)

Do not start until Lane T + Lane TI rows are all ≥ `passes local rerun`.

## Lane B — Bridge (classical ↔ nonclassical pairs)

Blocked on NC.

## Lane S — Spine

Blocked on NC completion.
