# Formal Sim Geometry Advancement Long Goal

Date: 2026-05-26

Status: controller locked. This goal is not permission to run scouts.

## Operating Truth

The active Phase 2 carrier-frontier is locally saturated at
`AO_multiplicity_pair_separation_K`.

Local scout success is checkpoint evidence only. It does not authorize a fresh
map, a new scout, or downstream geometry while route truth is red.

Current blockers:

- `phase2_seed_frontier_transition_decision_20260525.json` has
  `decision=blocked`.
- `validator_all_pass=false`.
- Wizard v4.2 is `BLOCKED` with `accepted_parent_count=0` and
  `accepted_child_count=0`.
- The Phase 2 matrix has 59 rows, 56 `contract_complete`, and 3 `killed`.
- Nine `contract_complete` rows have null or missing `receipt_path`.
- AO keeps Hopf/Weyl, terrain, substages, PEPS3D closure, flux, Xi/Phi0,
  Axis0, Holodeck/FEP, physics, IGT/game theory, and axes 7-12 blocked.

## Ordered Invariant

The controller must preserve this order:

1. Prove local saturation.
2. Repair structural route truth.
3. Advance geometry only after an external auditor confirms 1 and 2 are settled.

Do not optimize receipt count. Do not turn local result availability into
permission to continue. Do not synthesize missing receipts.

## Saturation Standard

Local saturation means no fresh Phase 2 carrier-frontier map is admissible from
the current matrix while:

- Wizard is blocked;
- the transition validator is false;
- complete rows still have null `receipt_path`;
- killed fresh order-gap routes remain unresolved warning signs.

`DD_pair_delete_interaction_K` and `Y_order_gap_K` are saturation warnings.
They show that fresh order-gap grinding is not a route-truth repair.

## Route-Truth Repair Standard

Structural route truth repair must happen without:

- new same-matrix rows;
- new candidate/blocker/frontier-style JSON beyond the authorized reset packet;
- receipt synthesis for null-path rows;
- row closure by adding criteria after the fact;
- direct matrix or transition mutation in a locked packet;
- scout execution;
- downstream geometry opening.

The repair should classify null-path rows honestly:

- rows with no `result_path` and no `receipt_path` need route-truth repair, not
  synthesized receipts;
- rows with `result_path` but null `receipt_path` may only be repaired after an
  owner-authorized pass confirms the result is the receipt for that exact row.

## External Auditor Gate

An auditor is accepted only if it provides:

- a separate runtime and subagent or receipt id;
- verdict;
- at least three exact prompt/repo citations;
- explicit checks for receipt grinding, scout prohibition, matrix mutation,
  weak-auditor handling, Wizard unblock prohibition, and null receipts.

Generic PASS, unavailable, or FAIL means the auditor route is not accepted and
the lock remains.

The current auditor attempt is blocked because `spawn_agent` returned
`agent thread limit reached`.

## Advancement Gate

Only after owner-authorized route-truth repair and accepted external audit may a
later packet propose a fresh map. A later fresh-map claim must use a different
carrier/probe family and must name the blocked downstream surface it could
unblock.

Entropy, Hopf/Weyl, terrain, substages, flux, Xi/Phi0, Axis0, physics, IGT, and
axes 7-12 remain discussion or future targets until admitted by explicit finite
maps with carrier anchors, controls, receipts, and downstream boundaries.

## Active Lock Artifacts

- `system_v5/ops/formal_scouts/phase2_controller_lock_20260526.json`
- `system_v5/ops/formal_scouts/phase2_AO_saturation_reset_20260526.json`
- `system_v5/ops/FORMAL_SIM_RECEIPT_GRINDING_POSTMORTEM_20260526.md`

