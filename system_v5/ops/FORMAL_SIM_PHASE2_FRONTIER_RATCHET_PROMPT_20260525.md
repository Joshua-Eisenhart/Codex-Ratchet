# Formal Sim Phase 2 Frontier Ratchet Prompt

Status: controller handoff prompt for the current post-Phase-1 failure state.
This is not a result, not a proof, and not a promotion artifact.

Use this prompt when the formal worker has:

```text
1. repaired Phase 1 working_geometry,
2. written phase1_to_phase2_transition_decision_20260525.json,
3. run one Phase 2 finite PEPS3D seed-carrier scout,
4. then stopped with "next admissible work is a Phase 2 frontier matrix or blocker."
```

That closeout is still a failure. A single Phase 2 seed scout is not a Phase 2
frontier. The next controller action is not to describe that a frontier matrix
would be useful. The next controller action is to create or repair that matrix
and continue the bounded Phase 2 ratchet.

```text
You are a fresh formal-scout controller/worker in:
/Users/joshuaeisenhart/Desktop/Codex Ratchet

The user has explicitly complained that prior workers keep stopping after one
bounded packet. Do not repeat that failure.

Current known state:

- Phase 1 finite probe/effect response-quotient geometry has a working geometry
  statement in:
  system_v5/ops/formal_scouts/phase1_frontier_matrix_20260525.json
- Phase 1 transition artifact exists:
  system_v5/ops/formal_scouts/phase1_to_phase2_transition_decision_20260525.json
- One Phase 2 seed scout exists:
  system_v5/ops/formal_scouts/sim_finite_peps3d_probe_effect_seed_carrier_gate_probe.py
  system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json

The remaining failure:

The previous worker stopped after one Phase 2 seed scout and said the next
admissible work is a Phase 2 frontier matrix or blocker. That is not enough.
If runtime remains, you must create or repair the Phase 2 frontier matrix and
continue inside Phase 2. If runtime is truly exhausted, you must write a
continuation_required artifact with the exact next prompt. Do not call the run
complete.

Sim-mode parallelism requirement:

Use maximum useful parallelism across independent bounded Phase 2 packets,
tool-surface audits, and model pools. Attempt multiple model pools when
available: Codex-native, Claude Bridge, Gemini/direct external routes, and
local tools. The runner and shared JSON writes remain controller-serial, but
planning, packet authoring, audit, and follow-up scouting should not collapse to
one model. If a pool is unavailable or stalls, record it as blocked, partial,
rerouted, or deferred with a concrete reason.

The Phase 2 frontier matrix or transition artifact must include a
`multi_model_parallelism` object with status `max_used`, `partial`, or
`blocked`, the independent packets/routes attempted, model pools
attempted/completed/blocked, blockers, and serial boundaries.

Read first, in this exact order:

1. AGENTS.md
2. CODEX.md
3. system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
4. system_v5/docs/LLM_CONTROLLER_CONTRACT.md
5. system_v5/docs/LEGO_SIM_CONTRACT.md
6. system_v5/docs/system_levels_20260525/10_BOUNDED_MAX_EXPLORATION_PROCESS_REPAIR.md
7. scripts/validate_bounded_max_exploration.py
8. system_v5/ops/FORMAL_SIM_CONTINUOUS_RATCHET_PROMPT_20260525.md
9. system_v5/ops/formal_scouts/phase1_frontier_matrix_20260525.json
10. system_v5/ops/formal_scouts/phase1_to_phase2_transition_decision_20260525.json
11. system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json

First answer the geometry, not the logs.

The current Phase 2 working geometry is only:

PEPS3D-anchored finite response-quotient carrier geometry.

Plain answer:

Phase 1 earned finite response quotients Q_P = S / ~_P. Phase 2 has only begun
to test whether those finite quotient/readout objects can be anchored on a
finite PEPS3D cell carrier K=(V,E,F,C) without collapsing into scalar labels,
dense closure, or unanchored geometry.

Finite map:

seed_K : (r_P(s), anchor) -> anchored local PEPS3D carrier signatures
anchor : local carrier object -> V union E union F union C
I_K(T) = finite site/edge/face/cell signatures without dense closure

Domain:

validated finite Phase 1 probe/effect response data plus a finite PEPS3D cell
carrier K=(V,E,F,C) with explicit site, edge, face, and cell anchors.

Codomain/output:

anchored finite PEPS3D local tensors/signatures and ablation readouts over
site, edge, face, and cell supports.

Earned so far:

- finite PEPS3D anchors exist for site, edge, face, and cell supports;
- scalar PEPS3D labels are rejected;
- no-anchor controls are rejected;
- edge-erased and order-erased controls are rejected;
- dense closure is not used as claim-bearing evidence;
- one stress path reached 64 PEPS3D sites with bond 4.

Not yet geometry:

- spinor/Hopf/Weyl geometry is not yet admitted;
- terrain placement is not yet admitted;
- operator substage cells are not yet admitted;
- PEPS/PEPS3D closure beyond the finite seed carrier is not yet admitted;
- flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, and axes 7-12
  remain blocked.

Do not open those downstream consumers from the seed receipt.

Required controller move:

Create or repair:

system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json

The matrix must have rows using the bounded frontier-row schema:

row_id
candidate_family
carrier
probe_or_effect_family
operator_or_path_witness
positive_case
negative_control
boundary_control
status
blocked_consumers
next_in_level_move

Initial Phase 2 rows should include at least these families, with statuses set
honestly as contract_complete, candidate, blocked, or killed:

1. admitted_seed_receipt:
   the existing finite_peps3d_probe_effect_seed_carrier receipt.

2. anchor_ablation_family:
   site-only, edge-erased, face-erased, cell-erased, and no-anchor controls.

3. dense_closure_rejection_family:
   prove the seed carrier remains finite/local and does not use dense full-state
   closure as evidence.

4. order_sensitive_local_path_family:
   test at least one finite noncommuting or order-sensitive local action on the
   PEPS3D seed carrier while keeping spinor/Hopf/Weyl blocked.

5. bond_site_stress_family:
   stress finite site and bond ranges within Phase 2 only, recording where
   bounded locality survives or fails.

6. graph_topology_cell_support_family:
   use relevant graph/topology tools only to certify the finite K=(V,E,F,C)
   support structure, not to claim terrain, flux, or physics.

7. spinor_density_compatibility_blocker_family:
   decide whether a torch-native spinor-derived density carrier can be opened
   next, or write the exact blocker. This is still Phase 2 carrier work, not
   Hopf/Weyl geometry.

If fewer than the required Phase 2 frontier rows are contract_complete, set:

post_threshold_action: "continue_active_level"

and include:

next_in_level_packet_set

with the next bounded packets to run. Then run the first admissible packet in
that set if runtime remains.

Do not write:

"next admissible work is a Phase 2 frontier matrix or blocker"

unless you actually wrote the Phase 2 frontier matrix or blocker artifact in
this run.

Validator use:

Use scripts/validate_bounded_max_exploration.py against the Phase 2 matrix and
the current Phase 2 receipts. If the matrix has fewer than the chosen minimum
contract-complete rows, report that as an active-level continuation state, not
as a successful closeout. Continue inside Phase 2 unless runtime is truly
exhausted.

The Phase 2 closeout is invalid unless the last controller-owned artifact is
one of:

1. an updated Phase 2 frontier matrix with next_in_level_packet_set and the
   next packet started;
2. a Phase 2 blocked-reason repair artifact;
3. a Phase 2 to next-level transition artifact after the Phase 2 frontier
   threshold is actually reached.

No Phase 3 transition is allowed until the Phase 2 frontier matrix has enough
contract-complete rows and working_geometry for Phase 2.

Forbidden closeouts:

- "next admissible work is a Phase 2 frontier matrix or blocker" when no matrix
  or blocker was written;
- "Phase 2 seed passed, no downstream work";
- command logs before geometry;
- file lists before geometry;
- "all_pass=true" as the lead answer;
- any answer that does not say what geometry is working and what is still not
  geometry.

Correct closeout order:

1. What geometry is working now.
2. Finite map/domain/codomain for that geometry.
3. What controls prove it is not label-only.
4. What is explicitly not yet geometry.
5. Current Phase 2 frontier matrix path and row status.
6. Validator result, including whether a red result means "continue active
   level" rather than "complete."
7. Exact next bounded Phase 2 packet started, or continuation_required artifact
   path with the exact next prompt.
8. Explicit statement: this is not terminal unless the user asked to stop.
```

## Rationale

The previous repair fixed the Phase 1 stopping failure but left the same
failure pattern alive at Phase 2. The formal ratchet needs a repeated level
loop:

```text
working geometry statement
+ finite frontier matrix
+ many bounded packets inside the level
+ graveyard/blocker rows
+ transition decision only after threshold
```

One downstream seed scout is useful evidence. It is not a frontier, not a
closeout, and not a reason to stop.
