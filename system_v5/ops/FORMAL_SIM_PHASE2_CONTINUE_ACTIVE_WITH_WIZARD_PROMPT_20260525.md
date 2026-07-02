# Formal Sim Phase 2 Continue-Active Wizard Prompt

Status: controller handoff prompt for the current Phase 2 stop-in-disguise
failure. This is not a result, not a proof, and not a promotion artifact.

Use this prompt when the formal worker reports:

```text
Phase 2 matrix is 8/8 contract_complete.
Transition artifact says decision = continue_active_level.
I did not open Phase 3.
The next bounded Phase 2 packet shape is in the transition artifact.
```

That is still a failed closeout if no next packet was started, no
continuation-required artifact was written, and no Wizard v4.2 receipt or
Wizard blocker was recorded.

```text
You are a fresh formal-scout controller/worker in:
/Users/joshuaeisenhart/Desktop/Codex Ratchet

The user has explicitly complained that workers keep stopping after a green
matrix or transition artifact. Do not repeat that failure.

Current state:

- Phase 2 working geometry is PEPS3D-anchored finite response-quotient carrier
  geometry.
- Phase 2 frontier matrix exists:
  system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json
- Phase 2 transition artifact exists:
  system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json
- That transition artifact says `decision: continue_active_level`.
- The previous closeout failed because it did not execute the continuation
  packet, did not write a continuation-required artifact, and did not include a
  Wizard v4.2 run receipt or Wizard blocker.

Read first, in this exact order:

1. AGENTS.md
2. CODEX.md
3. system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
4. system_v5/docs/LLM_CONTROLLER_CONTRACT.md
5. system_v5/docs/LEGO_SIM_CONTRACT.md
6. system_v5/docs/system_levels_20260525/10_BOUNDED_MAX_EXPLORATION_PROCESS_REPAIR.md
7. scripts/validate_bounded_max_exploration.py
8. system_v5/ops/FORMAL_SIM_PHASE2_FRONTIER_RATCHET_PROMPT_20260525.md
9. system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json
10. system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json
11. all three current Phase 2 result receipts:
    - system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json
    - system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json
    - system_v5/ops/formal_scouts/results/peps_peps3d_local_environment_contraction_gate_probe_results.json

First run the strict transition validator. It should fail on the current state:

python3 scripts/validate_bounded_max_exploration.py \
  --require-frontier-matrix \
  --min-contract-complete-rows 8 \
  --frontier-matrix system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json \
  --transition-artifact system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json \
  --require-transition-artifact \
  --require-transition-progress \
  --require-wizard-receipt \
  --require-multi-model-parallelism \
  --min-model-pools 2 \
  system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json \
  system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json \
  system_v5/ops/formal_scouts/results/peps_peps3d_local_environment_contraction_gate_probe_results.json

Expected current failures:

- transition_missing_next_packet_progress_or_continuation_artifact
- transition_missing_wizard_v4_2_receipt_or_blocker
- transition_multi_model_parallelism_invalid

Those are the bugs to repair. Do not ignore them.

Max-parallelism / multiple-model requirement:

Sim-mode work must use maximum useful parallelism across independent bounded
packets and multiple model pools. The Python runner may execute the final sim
serially, but authoring, audit, route checks, tool-surface scouting, and
follow-up scouting should fan out.

Attempt multiple model pools when available, including Codex-native parents,
Claude Bridge children, and Gemini/direct external scout lanes. If a pool is
unavailable, blocked, degraded, or times out, record that explicitly. Do not
convert a single-model run into "max parallelism" by prose.

Update the transition artifact with:

multi_model_parallelism: {
  "status": "max_used" | "partial" | "blocked",
  "independent_packets": [
    "phase2_anchor_ablation_boundary_stress_packet",
    "tool_surface_or_receipt_audit_packet",
    "validator_transition_gate_packet"
  ],
  "model_pools": [
    {
      "pool": "codex-native",
      "model": "...",
      "status": "completed" | "partial" | "blocked",
      "receipt_path": "... or not_applicable",
      "blocked_reason": "... or not_applicable"
    },
    {
      "pool": "claude-bridge",
      "model": "sonnet|opus|haiku",
      "status": "completed" | "partial" | "blocked",
      "receipt_path": "... or not_applicable",
      "blocked_reason": "... or not_applicable"
    },
    {
      "pool": "gemini",
      "model": "...",
      "status": "completed" | "partial" | "blocked",
      "receipt_path": "... or not_applicable",
      "blocked_reason": "... or not_applicable"
    }
  ],
  "blockers": [],
  "serial_boundaries": [
    "Python runner execution",
    "shared frontier/transition artifact write",
    "git/index mutation"
  ]
}

If status is `max_used`, at least two model pools must complete useful,
receipt-backed work. If status is `partial`, at least two model pools must be
attempted or the blockers must explain why they could not be. If status is
`blocked`, the blockers must be concrete enough for the next controller to fix.

Wizard requirement:

Run Wizard v4.2 for this continuation decision, or record an explicit Wizard
blocker. A controller-local prose explanation is not a Wizard run.

Preferred command if available:

python3 scripts/wizard_v4_2.py \
  --level low \
  --loop 1 \
  --compact-profile audit \
  --task "Phase 2 formal-scout continuation: verify continue_active_level requires next-packet progress, Wizard receipt/blocker, and no Phase 3 opening." \
  --out-dir /tmp/codex_ratchet_phase2_continue_active_wizard_20260525

If a full/high Wizard run is available and runtime permits, use high. If low or
compact is all that can complete, mark it PARTIAL. If Wizard cannot run, write
a blocker into the transition artifact:

wizard_v4_2: {
  "status": "BLOCKED",
  "blocked_reason": "...",
  "attempted_command": "..."
}

If Wizard runs, update the transition artifact with:

wizard_v4_2: {
  "status": "PARTIAL" | "FULL",
  "run_root": "...",
  "compiled_output_path": "... or not_applicable",
  "accepted_parent_count": <integer or null>,
  "accepted_child_count": <integer or null>,
  "gemini_status": "attempted" | "skipped" | "blocked" | "not_applicable"
}

Next packet requirement:

Because the transition decision is continue_active_level, you must not stop
after writing a prompt. Execute one bounded Phase 2 continuation packet now, or
write a continuation-required artifact if runtime is truly exhausted.

Next packet to start:

Phase 2 anchor-ablation / local-boundary stress continuation.

Write, run, and receipt one bounded packet under:

system_v5/ops/formal_scouts/sim_peps3d_anchor_ablation_boundary_stress_continuation_probe.py
system_v5/ops/formal_scouts/results/peps3d_anchor_ablation_boundary_stress_continuation_probe_results.json

Allowed finite maps:

A_K : anchored local carrier object -> site/edge/face/cell ablation response vector
B_K : finite local boundary neighborhood -> bounded boundary contraction signature

Required scope:

- Phase 2 finite PEPS3D seed-carrier continuation only.
- Keep domain finite.
- Keep codomain/output finite.
- Include PEPS3D site/edge/face/cell anchors.
- Include F01 finite carriers/probes/operators/paths.
- Include N01 order-sensitive or noncommuting witness, or an honest collapse.
- Include positive case, negative control, boundary control, and order-erased
  control.
- Keep dense-state and dense-environment closure banned as claim-bearing
  evidence.

Forbidden:

- nested Hopf tori;
- Weyl sheet cover;
- terrain generator placement;
- operator substage cells;
- PEPS/PEPS3D closure beyond bounded local seed-carrier evidence;
- flux;
- Xi/Phi0;
- Axis0;
- Holodeck/FEP;
- physics;
- IGT/game theory;
- axes 7-12;
- Phase 3 transition.

After running the packet, update:

system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json

Add one of:

started_next_packet: true
started_packet_path: "system_v5/ops/formal_scouts/sim_peps3d_anchor_ablation_boundary_stress_continuation_probe.py"
started_result_path: "system_v5/ops/formal_scouts/results/peps3d_anchor_ablation_boundary_stress_continuation_probe_results.json"

or, only if runtime is truly exhausted:

continuation_required_artifact_path: "system_v5/ops/formal_scouts/phase2_continue_active_continuation_required_20260525.json"

If blocked:

blocked_reason_or_repair_path: "system_v5/ops/formal_scouts/phase2_continue_active_blocker_20260525.json"

Then rerun the strict validator command above. It must pass before closeout, or
the closeout must say the run remains blocked and cite the failing violations.

Correct closeout order:

1. What Phase 2 geometry is working.
2. What active continuation packet was actually started or why it is blocked.
3. Wizard v4.2 status: FULL, PARTIAL, or BLOCKED, with run root or blocker.
4. Multi-model parallelism status: max_used, partial, or blocked, with model
   pools attempted/completed and blockers.
5. Finite map/domain/codomain of the new packet.
6. Controls and what remains not-geometry.
7. Strict validator result with transition-progress, Wizard, and multi-model
   checks.
8. Exact next bounded packet if one remains, or explicit blocked state.

Forbidden closeouts:

- "decision is continue_active_level" without starting the next packet;
- "next bounded packet shape" without a packet source/result or continuation artifact;
- "I did not open Phase 3" as the main result;
- command logs before geometry;
- file lists before geometry;
- no Wizard status;
- no multi-model parallelism status;
- no strict transition validator result.
```

## Why This Exists

The previous prompts fixed the first two stop failures but left a subtler one:
a worker can write a `continue_active_level` transition artifact and still stop.
That is invalid. `continue_active_level` means execute the next bounded packet,
write a continuation-required artifact, or write a blocker. It also means the
Wizard layer must either run with receipts or be explicitly blocked.
