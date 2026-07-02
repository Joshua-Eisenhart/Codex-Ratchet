# Formal Sim Continuous Ratchet Prompt

Status: controller handoff prompt for continuing after a bounded level reaches
its frontier threshold. This is not a result, not a proof, and not a promotion
artifact.

Use this prompt when a formal worker reports that an active level passed its
frontier validator and then stops. The stopping behavior is the failure being
repaired.

```text
You are a fresh formal-scout controller/worker in:
/Users/joshuaeisenhart/Desktop/Codex Ratchet

The user has explicitly complained that prior workers stop after one level or
after a green frontier matrix. Do not repeat that failure.

Read first, in this exact order:

1. AGENTS.md
2. CODEX.md
3. system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
4. system_v5/docs/LLM_CONTROLLER_CONTRACT.md
5. system_v5/docs/LEGO_SIM_CONTRACT.md
6. system_v5/docs/system_levels_20260525/10_BOUNDED_MAX_EXPLORATION_PROCESS_REPAIR.md
7. scripts/validate_bounded_max_exploration.py
8. system_v5/ops/formal_scouts/phase1_frontier_matrix_20260525.json
9. the result JSONs named by that frontier matrix

Core rule:

A green active-level frontier matrix is not permission to stop. It is a
controller transition gate.

Sim-mode parallelism rule:

A bounded level is not a single-model serial exercise. Use maximum useful
parallelism across independent bounded packets, tool surfaces, audit lanes, and
worker/model pools. The Python runner and shared artifact writes remain serial,
but planning, authoring, auditing, and follow-up scouting should fan out across
Codex-native, Claude Bridge, Gemini/direct external lanes, and local tools when
available. If a pool is unavailable, record it as blocked. Do not call a
single-model run max parallelism.

Every transition artifact must include `multi_model_parallelism` with:

status: "max_used" | "partial" | "blocked"
independent_packets
model_pools
blockers
serial_boundaries

Run:

python3 scripts/validate_bounded_max_exploration.py \
  --require-frontier-matrix \
  --min-contract-complete-rows 10 \
  --frontier-matrix system_v5/ops/formal_scouts/phase1_frontier_matrix_20260525.json \
  system_v5/ops/formal_scouts/results/phase1_finite_probe_effect_quotient_root_gate_probe_results.json \
  system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json \
  system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json \
  system_v5/ops/formal_scouts/results/sic_mub_probe_family_comparison_probe_results.json \
  system_v5/ops/formal_scouts/results/finite_contextuality_sheaf_event_gate_probe_results.json \
  system_v5/ops/formal_scouts/results/process_povm_quantum_comb_history_gate_probe_results.json \
  system_v5/ops/formal_scouts/results/finite_projective_design_spectral_triple_gate_probe_results.json

If validation is red because the frontier matrix lacks post-threshold
continuation fields, do not write another Phase 1 scout first. Add or repair
the controller-owned continuation fields:

post_threshold_action
next_controller_action
working_geometry
transition_artifact_path, if post_threshold_action = write_transition_artifact
next_in_level_packet_set, if post_threshold_action = continue_active_level
blocked_reason_or_repair_path, if post_threshold_action = blocked_with_repair

The `working_geometry` object is required. Include:

plain_answer
active_geometry_object
finite_map
domain
codomain_or_output
earned_structure
noncommuting_or_order_sensitive_structure
controls_that_hold
not_yet_geometry
next_geometry_question

Write this in plain English and concrete math, not as a command log. For the
current Phase 1 state, the expected object is a finite probe/effect
response-quotient geometry Q_P = S / ~_P plus finite projective/incidence and
history-effect probe-family geometries. Do not imply that PEPS3D, spinor/Hopf,
Weyl, terrain, substage, flux, Axis0, or physics geometry is working.

If Phase 1 receipts and the Phase 1 frontier matrix are green after that repair,
write exactly one controller-owned transition artifact:

system_v5/ops/formal_scouts/phase1_to_phase2_transition_decision_20260525.json

The transition artifact must include:

kind: "phase_transition_decision"
created_at
from_level: "phase_1_finite_probe_effect_quotient"
frontier_matrix_path
validator_command
validator_all_pass
contract_complete_rows
decision: "open_next_level" | "continue_active_level" | "blocked"
decision_reason
opened_level_or_blocked_level
next_worker_prompt
next_admissible_packet
working_geometry
blocked_downstream_consumers
not_a_stop: true

If the decision is "open_next_level", the next admissible packet is only:

Phase 2 finite PEPS3D seed-carrier scout.

That packet may not open spinor/Hopf/Weyl, terrain placement, operator
substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory,
or axes 7-12. It may only test whether a finite PEPS3D carrier anchor can
carry the already admitted Phase 1 finite probe/effect quotient.

If the transition artifact opens Phase 2 and runtime remains available, continue
immediately into one bounded Phase 2 seed-carrier scout. If runtime is exhausted,
emit the exact next worker prompt and mark the run as continuation_required, not
complete.

Forbidden closeout:

"Stopped at the correct boundary: Phase 1 only."

Correct closeout shape:

1. What geometry is working, in plain language.
2. What finite map/domain/codomain made it work.
3. What is not geometry yet and remains blocked.
4. Current active level and validator result.
5. Transition artifact path, or blocked-repair artifact path.
6. Multi-model parallelism status and model pools attempted/completed/blocked.
7. If opened, exact next bounded packet started or exact next prompt emitted.
8. Explicit statement: this is not a terminal stop unless the user asked to stop.

Forbidden closeout style:

1. file list first
2. command list first
3. "all_pass=true" first
4. "stopped at correct boundary" first
5. no answer to "what geometry is actually working?"
```

## Rationale

The old reset prompt was useful for preventing downstream contamination, but it
trained workers to interpret "Phase 1 only" as terminal. That is wrong for
ratchet operation. A bounded level has a boundary, but the controller must keep
the ratchet moving by transition, continued in-level exploration, or an explicit
blocker.
