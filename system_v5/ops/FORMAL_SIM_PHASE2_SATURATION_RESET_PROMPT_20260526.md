# Formal Sim Phase 2 Saturation Reset Prompt - 2026-05-26

Use this prompt for a fresh formal-sim controller thread. It is intentionally a
controller-repair packet, not a scout packet.

## Copy-Paste Prompt

```text
You are in /Users/joshuaeisenhart/Desktop/Codex Ratchet.

Task: repair the failed formal-sim control loop. Do not run a scout. Produce: controller lock/reset, new long-running formal goal, and receipt-grinding postmortem.

Read first: AGENTS.md, CODEX.md, the three process docs, system_v5/ops/SIM_FULL_WIZARD_PARALLEL_RUNBOOK.md, ~/wiki/wizard/packet-v4-2-current/WIZARD_v4_2.md, phase2_peps3d_seed_frontier_matrix_20260525.json, phase2_seed_frontier_transition_decision_20260525.json, phase2_post_AO_multiplicity_pair_separation_active_frontier_blocker_20260526.json.

Verify live facts: transition blocked; validator_all_pass=false; Wizard BLOCKED with 0 accepted parents/children; 56/59 rows complete, 3 killed; some complete rows have null receipt_path; matrix pointer may be stale; AO keeps Hopf/Weyl, terrain, substages, PEPS3D closure, flux, Xi/Phi0, Axis0, physics, IGT, axes 7-12 blocked; DD_pair_delete_interaction_K and Y_order_gap_K killed fresh order-gap paths.

Hard rule: local scout success is checkpoint evidence only. While Wizard is BLOCKED, validator is false, or null receipt_path rows exist, fresh-map and scout paths are unavailable. Repair completion is not continuation permission; any later scout requires owner authorization after this packet closes.

Receipt grinding means: new same-matrix row, new candidate/blocker/frontier-style JSON, receipt synthesis for null-path rows, or row closure by added criteria instead of retired criteria. It is forbidden here.

Allowed writes only: phase2_controller_lock_20260526.json; phase2_AO_saturation_reset_20260526.json; FORMAL_SIM_GEOMETRY_ADVANCEMENT_LONG_GOAL_20260526.md; FORMAL_SIM_RECEIPT_GRINDING_POSTMORTEM_20260526.md. Do not edit matrix/transition/source/result files in this packet. Put required matrix/transition repairs into the reset artifact as proposed diffs only.

Required work:
1. Write lock with scout_permitted=false, phase2_saturated=true, and wizard_unblock_self_declared=false.
2. In the reset artifact, list null receipt rows and stale pointers as proposed diffs with exact row_ids/fields. Do not regenerate receipts or apply diffs here.
3. Default: Phase 2 carrier-frontier locally saturated at AO. Fresh-map claim is unavailable while route truth is red. Later fresh-map claims require different carrier/probe family plus a named blocked downstream surface they can unblock.
4. Write long-running formal goal. Ordered invariant: prove local saturation, then repair structural route truth, then advance geometry only after external auditor confirms 1 and 2 are settled. Never optimize receipt count.
5. Write postmortem naming the root-cause chain: blocked Wizard -> local validator substitution -> not_a_stop -> candidate-discovery loop -> receipt grinding. Name DD and Y_order_gap as saturation warnings.
6. Run one fresh independent auditor route with separate receipt/runtime/subagent id. Accept auditor only if it returns verdict, >=3 exact prompt/repo citations, and checks: grinding, scout, matrix mutation, weak-auditor, Wizard unblock, null receipts. Generic PASS, unavailable, or FAIL => record blocker and close; do not weaken gates.

Validation: lint/JSON checks on the four written artifacts; run validate_bounded_max_exploration.py as read-only evidence only. Validator green cannot override the lock/Wizard/owner gate. Re-read lock and confirm scout_permitted=false. Report exact commands, pass/fail, blocker paths.

Forbidden: no new scout, candidate/discovery/frontier/blocker JSON beyond named reset files; no direct matrix/transition mutation; no downstream geometry claims; no FULL/PARTIAL Wizard claim without v4.2 receipts; no “not a stop” language; no self-declared Wizard unblock.

Allowed final state: controller locked with saturation/reset artifacts forbidding scouts until owner-authorized route-truth repair; or external auditor CLEAN plus validator evidence, still with scout_permitted=false.
```

## Test Checklist

- Contains all three requested outputs: controller reset, long-running goal,
  postmortem.
- Blocks new scouts while Wizard/validator/receipt-path truth is red.
- Forces saturation as a valid outcome.
- Keeps saturation as the default outcome while current route truth is red.
- Names the observed saturation warnings: `DD_pair_delete_interaction_K` and
  `Y_order_gap_K`.
- Separates local receipt validity from geometry advancement.
- Keeps downstream geometry blocked unless lower maps are actually earned.
- Defines and forbids receipt grinding operationally.
- Requires an independent auditor for the premortem closure.
