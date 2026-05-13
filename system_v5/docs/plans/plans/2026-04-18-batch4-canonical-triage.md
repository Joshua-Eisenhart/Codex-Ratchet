# 2026-04-18 Batch 4 — Canonical Conformance Triage Output

Status: DERIVED TRIAGE OUTPUT (no code edits yet, no label changes yet)

Companion files:
- queue: `system_v5/docs/plans/plans/2026-04-18-canonical-conformance-repair-queue.md`
- source audit: `~/wiki/projects/codex-ratchet/canonical_conformance_audit.md` (63 violators)
- broad plan: `system_v5/docs/plans/plans/2026-04-18-sim-estate-audit-and-plan.md`

Rule applied (from queue):
- `repair_in_place` = local or tool-capability packet, plausible bounded object, likely honest tool path.
- `demote_now` = overlay / companion / translation / matrix / trap / worldview / coupling-of-worldviews packet — too broad or too meta to be current-process canonical.
- `needs_owner_decision` = salvageable, but owner role is not obvious enough to auto-repair.

No probe is edited, renamed, or reclassified in-repo by this file. This is the triage; the label/demote/repair actions are separate steps that require owner confirmation and fresh reruns before any truth-surface promotion.

---

## Summary

- total violators: 63
- `demote_now`: 28
- `repair_in_place`: 19
- `needs_owner_decision`: 16

Bucket totals sum to 63.

---

## Bucket A — `demote_now` (28)

Default stance: demote unless a direct bounded owner role is shown. Reason after each.

1. `sim_engine_lab_alignment_overlay.py` — overlay/alignment surface, not a bounded owner.
2. `sim_cycle_protocol_receipt_status_matrix.py` — matrix/meta surface, not a canonical owner.
3. `sim_engine_lab_translation_targets.py` — translation surface, not canonical-owner-shaped.
4. `sim_qit_engine_companion_array.py` — companion array, support role, not canonical-owner.
5. `sim_qit_entropy_companion_array.py` — companion array, support role, not canonical-owner.
6. `sim_qit_moloch_coordination_trap.py` — worldview/narrative packet, not bounded-object canonical.
7. `sim_qit_predictive_world_model.py` — world-model narrative, not bounded-object canonical.
8. `sim_qit_repair_comparison_surface.py` — comparison surface, support role.
9. `sim_weyl_geometry_alignment_overlay.py` — overlay surface, not bounded owner.
10. `sim_weyl_geometry_translation_targets.py` — translation surface, not bounded owner.
11. `sim_layer_triple_catalog.py` — catalog/index surface, not owner.
12. `sim_weyl_two_model_crosscheck.py` — crosscheck, support role.
13. `sim_couple_holodeck_fep.py` — worldview-coupling packet, not bounded owner.
14. `sim_couple_holodeck_igt.py` — worldview-coupling packet.
15. `sim_couple_holodeck_leviathan.py` — worldview-coupling packet.
16. `sim_couple_igt_fep.py` — worldview-coupling packet.
17. `sim_couple_igt_sci_method.py` — worldview-coupling packet.
18. `sim_couple_leviathan_sci_method.py` — worldview-coupling packet.
19. `sim_coupling_fep_holodeck.py` — worldview-coupling packet.
20. `sim_coupling_fep_sci_method.py` — worldview-coupling packet.
21. `sim_coupling_holodeck_igt.py` — worldview-coupling packet.
22. `sim_coupling_holodeck_leviathan.py` — worldview-coupling packet.
23. `sim_coupling_holodeck_sci_method.py` — worldview-coupling packet.
24. `sim_coupling_igt_sci_method.py` — worldview-coupling packet.
25. `sim_coupling_leviathan_sci_method.py` — worldview-coupling packet.
26. `sim_weyl_geometry_ladder_audit.py` — audit/ladder surface, not bounded owner; more like Lane C maintenance than Lane B canonical.
27. `sim_3qubit_dag_formal_ordering.py` — formal-ordering study; superseded by `_v2`. Demote v1.
28. `sim_substrate_insensitive_analysis.py` — analysis overlay, meta surface; owner role ambiguous → default demote; flagged also in owner-decision below (kept in demote by default per queue rule “demote unless owner role shown”).

Meaning: these 28 shrink the canonical set by honest relabel, not by repair. Demote to `classical_baseline` or remove the `canonical` classification field pending owner confirmation.

---

## Bucket B — `repair_in_place` (19)

Candidates worth saving if packet fields and tool role can be made honest. For each: what to fix.

1. `sim_foundation_shell_graph_topology.py` — add `positive_tests` / `negative_tests` / `boundary_tests` around bounded graph/topology packet assertions; verify tool role is graph-native, not numpy fallback.
2. `sim_operator_geometry_compatibility.py` — add the three test sections; verify the operator-vs-geometry compatibility claim has a real load-bearing tool (z3 or Cl(3)/Cl(6) rotor) not string labels.
3. `sim_compound_operator_geometry.py` — add test sections; verify composition honesty.
4. `sim_z3_channel_composition_boundary.py` — add test sections; z3 already load-bearing, so low-risk field fill.
5. `sim_z3_fence_exhaustive_negatives.py` — add test sections; z3 load-bearing.
6. `sim_qit_strong_coupling_landauer.py` — add test sections; verify Landauer bound enforcement is real, not labelled.
7. `sim_pure_lego_pairwise_shell_coupling_cp1.py` — add test sections; CP1 pairwise is inside the admitted local spine.
8. `sim_pure_lego_qfi_wy_qgt.py` — add test sections; QFI/WY/QGT are on the admitted tools list.
9. `sim_lego_weyl_hypergraph_local.py` — add test sections; Weyl local packet is Lane B spine.
10. `sim_clifford_generator_basis.py` — add `load_bearing` + test sections; Clifford basis is lego foundation.
11. `sim_pauli_algebra_relations.py` — add `load_bearing` + test sections; Pauli algebra is lego foundation.
12. `sim_pauli_generator_basis.py` — add `load_bearing` + test sections; sibling of clifford_generator_basis.
13. `sim_lego_weyl_pauli_transport.py` — add `load_bearing`; verify transport is via real operator not labels.
14. `sim_holographic_clifford_pairwise_coupling.py` — add `load_bearing`; verify Cl(n) rotor is load-bearing, not numpy fallback.
15. `sim_weyl_holo_symplectic_topology_variants.py` — add `load_bearing`; verify topology variant test uses TopoNetX or real topology library.
16. `sim_arakelov_intersection_constraint_canonical.py` — add `load_bearing`; verify the named tool is actually carrying the intersection constraint, else demote.
17. `sim_axis_couple_0_6_entropy_gradient_x_action_orientation.py` — add `load_bearing`; borderline (could move to owner-decision if owner disagrees with axis-couple honesty).
18. `sim_beilinson_regulator_constraint_canonical.py` — add `load_bearing`; verify tool role is real, else demote.
19. `sim_chern_weil_torch_foundation.py` — add test sections; foundation-shaped; verify torch tool role is load-bearing.

Rule reminder: do not just fill the `load_bearing` field. If the named tool is not really carrying the claim, the correct action is `demote_now`, not cosmetic repair.

---

## Bucket C — `needs_owner_decision` (16)

Salvageable, but owner must decide role before any repair:

1. `sim_axis6_canonical.py` — axis work; owner doctrine says axes are hypotheses, not canon. Decide: stay canonical, convert to axis-candidate, or demote.
2. `sim_phase7_baseline_validation.py` — phase-7 is a legacy framing. Decide: keep as `classical_baseline`, archive, or retire.
3. `sim_probe_object.py` — probe_object is a root concept in doc 17 (`not_normalized_yet`). Decide: treat as tool-capability packet, lego foundation, or demote.
4. `sim_substrate_insensitive_analysis.py` — (also listed in demote pending owner confirm)
5. `sim_geomstats_ratchet_trajectory.py` — ratchet-trajectory is theory-heavy. Decide: tool-capability sim for geomstats, or demote.
6. `sim_entanglement_spectrum.py` — spectrum measure; decide whether it is a canonical entropy-family owner or a support diagnostic.
7. `sim_pure_lego_hypothesis_testing.py` — meta-level lego. Decide: tool-capability, lego-process, or demote.
8. `sim_3qubit_dag_formal_ordering_v2.py` — keep the v2 if the ordering claim has a bounded owner; else demote.
9. `sim_constraint_manifold_L0_L1.py` — L0/L1 manifold packet; owner doctrine: manifold is primary. Decide: make into canonical foundation packet or demote as illustrative.
10. `sim_constraint_manifold_L2_L3.py` — sibling of L0_L1.
11. `sim_chern_weil_spin_geometry_mera_weyl_coupling_canonical.py` — bundled multi-family name; decide whether to split per doc 17 or demote.
12. `sim_quillen_theorem_muf_universal_constraint_canonical.py` — theorem-named canonical. Decide: real bounded owner for Quillen constraint, or demote.
13. `sim_qutip_classical_bridge_density_roundtrip.py` — bridge/roundtrip between qutip and classical; decide tool-capability vs bridge-claim (bridge is gated).
14. `sim_riemannian_connection_holonomy_fiber_assoc_moment_index_chern_8shell_coupling_canonical.py` — multi-family bundled name; must be split or demoted.
15. `sim_riemannian_torch_foundation.py` — if torch-foundation is load-bearing and bounded, repair; else demote.
16. `sim_spinor_riemannian_hopf_coupling_canonical.py` — bundled multi-layer coupling; split per doc 17 or demote.
17. `sim_spinor_torch_foundation.py` — foundation-shaped; same test as riemannian_torch_foundation.

(16 listed; `sim_substrate_insensitive_analysis.py` is double-listed with demote as its default — owner decision determines which bucket it lands in.)

---

## Effect on truth surfaces

- `sim_truth_audit.md`: unchanged until fresh reruns justify.
- `16_lego_build_catalog.md`: no label flips from this file.
- `17_actual_lego_registry.md`: bundled names (e.g. Chern–Weil + spin + MERA + Weyl; Riemannian + connection + holonomy + fiber + moment-index + Chern + 8-shell) surface as row-split candidates per doc 17's no-sub-lego rule.

## Next action (still within Batch 4)

1. Owner confirms the 16-item `needs_owner_decision` list.
2. Owner confirms the 28-item demotion list or moves specific probes into repair.
3. Then (and only then) execute the mechanical demotions and repair-in-place edits, rerun, and record fresh reruns before any truth-label promotion.

## Meaning Now

Batch 4's triage is done. 63 violators are now 28 demotion-default + 19 repair-default + 16 owner-decision. No code has been changed, no truth labels flipped. This file is the honest classification; the label/demote/repair operations are the next step and are owner-gated.
