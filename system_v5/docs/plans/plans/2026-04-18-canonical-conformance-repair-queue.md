# 2026-04-18 Canonical Conformance Repair Queue

Status: DERIVED EXECUTION QUEUE

Use this file with:
- `system_v5/docs/plans/plans/2026-04-18-sim-estate-audit-and-plan.md`
- `system_v5/docs/plans/plans/sim_backlog_matrix.md`
- `system_v5/docs/plans/plans/sim_process_gap_log.md`

Goal: turn the `63` current canonical-conformance violations into an executable repair/demotion queue instead of a generic cleanup intention.

Source:
- `~/wiki/projects/codex-ratchet/canonical_conformance_audit.md`

## Failure clusters

- `39` probes: missing `positive_tests`, `negative_tests`, `boundary_tests`
- `15` probes: missing `load_bearing`, `positive_tests`, `negative_tests`, `boundary_tests`
- `6` probes: missing `load_bearing` only
- `2` probes: missing `positive_tests` only
- `1` probe: missing `positive_tests`, `negative_tests`

## Queue rule

Do not treat every violator the same.

Split each file into one of:
- `repair_in_place`
- `demote_now`
- `needs_owner_decision`

Use these heuristics:
- `repair_in_place`: local or tool-capability packet with a plausible bounded object and likely honest tool path
- `demote_now`: overlay / companion / translation / matrix / trap / worldview packet that is obviously too broad or too meta to be current-process canonical
- `needs_owner_decision`: family where the packet might be worth saving, but the intended owner role is ambiguous

## Wave 1 — Fast demotion candidates

These look more like support, overlay, translation, or comparison surfaces than honest canonical packets. Default stance: demote unless a direct bounded owner role is shown.

- `sim_engine_lab_alignment_overlay.py`
- `sim_cycle_protocol_receipt_status_matrix.py`
- `sim_engine_lab_translation_targets.py`
- `sim_qit_engine_companion_array.py`
- `sim_qit_entropy_companion_array.py`
- `sim_qit_moloch_coordination_trap.py`
- `sim_qit_predictive_world_model.py`
- `sim_qit_repair_comparison_surface.py`
- `sim_weyl_geometry_alignment_overlay.py`
- `sim_weyl_geometry_translation_targets.py`
- `sim_layer_triple_catalog.py`
- `sim_weyl_two_model_crosscheck.py`
- the Holodeck / IGT / Leviathan coupling cluster:
  - `sim_couple_holodeck_fep.py`
  - `sim_couple_holodeck_igt.py`
  - `sim_couple_holodeck_leviathan.py`
  - `sim_couple_igt_fep.py`
  - `sim_couple_igt_sci_method.py`
  - `sim_couple_leviathan_sci_method.py`
  - `sim_coupling_fep_holodeck.py`
  - `sim_coupling_fep_sci_method.py`
  - `sim_coupling_holodeck_igt.py`
  - `sim_coupling_holodeck_leviathan.py`
  - `sim_coupling_holodeck_sci_method.py`
  - `sim_coupling_igt_sci_method.py`
  - `sim_coupling_leviathan_sci_method.py`

Why first:
- these are the lowest-cost honesty wins
- many appear structurally support-like rather than canonical-owner-like

## Wave 2 — Repair-in-place local / tool packets

These look like packets worth saving if the packet fields and tool role can be made honest.

- `sim_foundation_shell_graph_topology.py`
- `sim_operator_geometry_compatibility.py`
- `sim_compound_operator_geometry.py`
- `sim_z3_channel_composition_boundary.py`
- `sim_z3_fence_exhaustive_negatives.py`
- `sim_qit_strong_coupling_landauer.py`
- `sim_pure_lego_pairwise_shell_coupling_cp1.py`
- `sim_pure_lego_qfi_wy_qgt.py`
- `sim_lego_weyl_hypergraph_local.py`
- `sim_clifford_generator_basis.py`
- `sim_pauli_algebra_relations.py`
- `sim_pauli_generator_basis.py`
- `sim_lego_weyl_pauli_transport.py`
- `sim_holographic_clifford_pairwise_coupling.py`
- `sim_weyl_holo_symplectic_topology_variants.py`

Why second:
- these are closer to the admitted local spine or direct successor work
- if repaired honestly, they can improve the real foundation instead of only shrinking debt

## Wave 3 — Needs-owner-decision packets

These may be salvageable, but the intended owner role is not obvious enough to auto-repair.

- `sim_axis6_canonical.py`
- `sim_axis_couple_0_6_entropy_gradient_x_action_orientation.py`
- `sim_phase7_baseline_validation.py`
- `sim_probe_object.py`
- `sim_substrate_insensitive_analysis.py`
- `sim_geomstats_ratchet_trajectory.py`
- `sim_entanglement_spectrum.py`
- `sim_pure_lego_hypothesis_testing.py`

Why third:
- these risk turning into fake-good repairs if handled mechanically
- decide first whether each should remain canonical-targeted, become supporting, or be retired

## Wave 4 — Narrow pure-load-bearing fixes

These are missing `load_bearing` only and are the cleanest field-level audit targets.

- `sim_arakelov_intersection_constraint_canonical.py`
- `sim_axis_couple_0_6_entropy_gradient_x_action_orientation.py`
- `sim_beilinson_regulator_constraint_canonical.py`
- `sim_holographic_clifford_pairwise_coupling.py`
- `sim_lego_weyl_pauli_transport.py`
- `sim_weyl_holo_symplectic_topology_variants.py`

Rule:
- do not just fill the manifest
- verify whether the named tool is really carrying the claim or whether the file should be demoted instead

## Output expected from Batch 4

For each of the `63`:
- current failure type
- proposed action: `repair_in_place` / `demote_now` / `needs_owner_decision`
- short reason
- if repairing: exact missing packet fields or tool-role correction needed

## Meaning Now

The canonical-debt batch is no longer “audit the 63.” It is a staged honesty queue with obvious demotion-first and repair-first waves.
