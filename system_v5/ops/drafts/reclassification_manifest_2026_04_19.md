# Reclassification manifest — 2026-04-19

**Source:** DONE rows from `system_v5/ops/queue_default.txt` as of 2026-04-19 runtime snapshot (~02:3x).

**Method:** six-bucket cascade from [feedback_tool_stage_admission_and_skip_ahead_contract.md](~/.claude/projects/-Users-joshuaeisenhart-Desktop-Codex-Ratchet/memory/feedback_tool_stage_admission_and_skip_ahead_contract.md).

**Classifier:** `/tmp/classify_done.py` (structural pattern check on probe file: `classification`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH` substring `load_bearing`, basename prefixes).

## Distribution

| bucket | count | % | destination |
|---|---|---|---|
| `b1_t4_ledger` | 97 | 38% | migrate → **ledger diff on `TOOL_CAPABILITY_AND_INTEGRATION_LEDGER.md`** as integration-depth evidence per tool. These 97 declared `load_bearing` but ran WITHOUT a BOUND block — routing failure. Attribute to loopback target manually. |
| `b2_t1t2_capability` | 0 | 0% | migrate → per-tool capability row in ledger. Zero rows matched `sim_capability_*` prefix — capability probes live in `queue_tier_a.txt` already. |
| `b3_orphan_classical` | 90 | 36% | tag `orphan_no_loopback` + archive → `queue_disposal.txt`. classical_baseline + all tools None; no admissibility evidence. |
| `b4_lego_local` | 12 | 5% | relocate → `queue_lego_backlog.txt`. Canonical-classified but no load-bearing tool claim. |
| `b5_offlane` | 26 | 10% | relocate → `queue_offlane.txt`. Leviathan / off-program. |
| `b6_malformed` | 27 | 11% | retire → `queue_disposal.txt`. Missing probe file, no `classification`, or no `TOOL_MANIFEST` assignment. |
| **total** | **252** | | |

## The routing failure, quantified

**97 rows (38%) declared `load_bearing` integration-depth** and were drained through `queue_default.txt` without an 8-field BOUND block, without a loopback-writeback assertion, and without a ledger row update. Every one violates [28_bounded_work.md](~/wiki/harness/28_bounded_work.md) lines 115-122 admission-pool-not-pipeline spec.

The drained rows were real work. The routing was wrong.

## Ledger-diff candidates (bucket 1)

These rows need a per-tool integration-depth row update on `system_v5/docs/plans/plans/TOOL_CAPABILITY_AND_INTEGRATION_LEDGER.md`. Load-bearing tool should be extracted from each probe's `TOOL_INTEGRATION_DEPTH` dict.

- `sim_assoc_bundle_hopf_frame_bundle_carrier|cls=canonical`
- `sim_baseline_density_eigendecomp|cls=classical_baseline`
- `sim_cirq_capability|cls=canonical`
- `sim_cl3_basis|cls=classical_baseline`
- `sim_cl3_bivector_exp|cls=classical_baseline`
- `sim_cl3_composition|cls=classical_baseline`
- `sim_cl3_invariants|cls=classical_baseline`
- `sim_cl3_reflection|cls=classical_baseline`
- `sim_cl3_rotor_product|cls=classical_baseline`
- `sim_cl6_basis|cls=classical_baseline`
- `sim_cl6_chirality|cls=classical_baseline`
- `sim_cl6_rotor_product|cls=classical_baseline`
- `sim_cl6_spin_group_embedding|cls=classical_baseline`
- `sim_clifford_torch_foundation|cls=canonical`
- `sim_contact_torch_foundation|cls=canonical`
- `sim_cramer_rao_bound_classical|cls=classical_baseline`
- `sim_dirac_mera_holographic_torch_canonical|cls=canonical`
- `sim_dirac_torch_foundation|cls=canonical`
- `sim_entropy_bregman_crosscouple_classical|cls=classical_baseline`
- `sim_f01_compose_12_tensor_product_preserves_finiteness|cls=canonical`
- `sim_f01_compose_13_partial_trace_preserves_distinguishability_bound|cls=canonical`
- `sim_f01_compose_14_iterated_measurement_saturates_log_N|cls=canonical`
- `sim_f01_compose_15_quotient_cardinality_le_original|cls=canonical`
- `sim_f01_cross_09_z3_cvc5_parity_probe_bound|cls=canonical`
- `sim_f01_cross_10_clifford_rotor_distinguishability|cls=canonical`
- `sim_f01_cross_11_pytorch_autograd_distinguishability_loss|cls=canonical`
- `sim_f01_deep_01_probe_size_lower_bound_log2_N|cls=canonical`
- `sim_f01_deep_02_finiteness_forces_discrete_spectrum|cls=canonical`
- `sim_f01_deep_03_information_bound_shannon_log_N_max|cls=canonical`
- `sim_f01_deep_04_distinguishability_quantum_nonzero|cls=canonical`
- `sim_f01_deep_05_probe_reuse_compresses_capacity|cls=canonical`
- `sim_f01_fail_06_continuum_distinguishability_contradiction|cls=canonical`
- `sim_f01_fail_08_no_finite_hilbert_no_trace_class|cls=canonical`
- `sim_f01n01_couple_clifford_rotor_identity_under_finite_probes|cls=canonical`
- `sim_f01n01_couple_cvc5_parity_on_joint_bound|cls=canonical`
- `sim_f01n01_couple_finite_classes_excludes_continuum|cls=canonical`
- `sim_f01n01_couple_indistinguishable_saturates_probe_capacity|cls=canonical`
- `sim_f01n01_couple_noncommute_requires_distinct_probes|cls=canonical`
- `sim_f01n01_couple_probe_refinement_bounded_by_log_N|cls=canonical`
- `sim_f01n01_couple_quotient_respects_cardinality_bound|cls=canonical`
- `sim_f01n01_lego_01_rank_distinguishability|cls=canonical`
- `sim_f01n01_lego_02_noncommutation_propagation|cls=canonical`
- `sim_f01n01_lego_03_identity_via_indistinguishability_mixed|cls=canonical`
- `sim_f01n01_lego_04_partial_trace_bounds|cls=canonical`
- `sim_f01n01_lego_05_cl_rotor_pair|cls=canonical`
- `sim_f01n01_lego_06_unsat_max_mixed_self_conj|cls=canonical`
- `sim_f01n01_lego_07_abc_vs_acb|cls=canonical`
- `sim_f01n01_lego_08_equiv_class_cardinality_2q|cls=canonical`
- `sim_f01n01_lego_09_probe_size_lower_bound|cls=canonical`
- `sim_f01n01_lego_10_n01_commutator_zero_equivalence|cls=canonical`
- `sim_fep_atom_5_distinguishability|cls=canonical`
- `sim_fiber_bundle_triviality_classical|cls=classical_baseline`
- `sim_geom_noncomm_bch_nonzero_commutator|cls=canonical`
- `sim_geom_noncomm_chirality_then_fiber_winding|cls=canonical`
- `sim_geom_noncomm_e3nn_irrep_compose_order|cls=canonical`
- `sim_geom_noncomm_hopf_fiber_then_weyl_projector|cls=canonical`
- `sim_geom_noncomm_pauli_x_then_z_fails_id|cls=canonical`
- `sim_geom_noncomm_so3_reduction_then_u1_phase|cls=canonical`
- `sim_geom_noncomm_spin_double_cover_then_reflection|cls=canonical`
- `sim_geom_noncomm_z3_unsat_order_swap|cls=canonical`
- `sim_gerbe_admissibility_dixmier_douady|cls=canonical`
- `sim_gerbe_carrier_cell_complex|cls=canonical`
- `sim_gerbe_contact_clifford_torch_canonical|cls=canonical`
- `sim_gerbe_distinguishability_holonomy|cls=canonical`
- `sim_gerbe_reduction_coboundary|cls=canonical`
- `sim_gerbe_structure_b_field_cochain|cls=canonical`
- `sim_gerbe_torch_foundation|cls=canonical`
- `sim_ghz_mermin_inequality_canonical|cls=canonical`
- `sim_gudhi_torus_betti_canonical|cls=canonical`
- `sim_hellinger_categorical_classical|cls=classical_baseline`
- `sim_hopf_symplectic_contact_torch_canonical|cls=canonical`
- `sim_hopf_torch_foundation|cls=canonical`
- `sim_kahler_torch_foundation|cls=canonical`
- `sim_mera_torch_foundation|cls=canonical`
- `sim_mle_consistency_bernoulli_classical|cls=classical_baseline`
- `sim_no_cloning_theorem_canonical|cls=canonical`
- `sim_numpy_capability|cls=canonical`
- `sim_pennylane_capability|cls=canonical`
- `sim_probe_object_classical|cls=classical_baseline`
- `sim_qutip_capability|cls=canonical`
- `sim_rustworkx_apsp_constraint_skeleton|cls=canonical`
- `sim_rustworkx_scc_admissibility|cls=canonical`
- `sim_scipy_capability|cls=canonical`
- `sim_shannon_entropy_bernoulli_sweep_classical|cls=classical_baseline`
- `sim_symplectic_torch_foundation|cls=canonical`
- `sim_sympy_campbell_pauli|cls=canonical`
- `sim_sympy_charpoly_eigvals|cls=canonical`
- `sim_sympy_det_product_4x4|cls=canonical`
- `sim_sympy_gaussian_integral|cls=canonical`
- `sim_sympy_jacobi_su2|cls=canonical`
- `sim_sympy_partial_fraction|cls=canonical`
- `sim_sympy_schur_complement_psd|cls=canonical`
- `sim_torch_ga_capability|cls=canonical`
- `sim_torch_mi_dephasing_primitive|cls=canonical`
- `sim_tsallis_q_sweep_classical|cls=classical_baseline`
- `sim_tv_contraction_dpi_classical|cls=classical_baseline`
- `sim_weyl_torch_foundation|cls=canonical`

## Archive candidates (buckets 3, 5, 6)

### bucket 3 orphan_classical (90)

- `sim_admissibility_manifold_mc_classical`
- `sim_baseline_bloch_vector`
- `sim_baseline_dephasing_channel`
- `sim_baseline_partial_trace_2x2`
- `sim_baseline_purity_depolarizing`
- `sim_blackwell_comparison_classical`
- `sim_branch_weight`
- `sim_branch_weight_classical`
- `sim_carrier_probe_support_classical`
- `sim_channel_cptp_classical`
- `sim_characteristic_representation_classical`
- `sim_choi_matrix_classical`
- `sim_coarse_grained_operator_algebra_classical`
- `sim_coherence_measure_classical`
- `sim_commutative_geometry_collapse`
- `sim_conditional_entropy_classical`
- `sim_conditional_mutual_information_classical`
- `sim_constraint_probe_admissibility_classical`
- `sim_contextuality_witness_classical`
- `sim_correlation_tensor_principal_directions_classical`
- `sim_covariance_operator_classical`
- `sim_cross_fep_x_igt`
- `sim_cross_fep_x_science_method`
- `sim_cross_holodeck_x_igt`
- `sim_cross_science_method_x_leviathan`
- `sim_data_processing_inequality_classical`
- `sim_distinguishability_relation_classical`
- `sim_eigenvalue_spectrum_view_classical`
- `sim_entanglement_distillation_classical`
- `sim_entanglement_of_formation_classical`
- `sim_f01_finitude_constraint_classical`
- `sim_fep_generative_model_as_shell`
- `sim_fep_minimization_as_g_reduction`
- `sim_fep_pair_active_inference_x_markov_blanket`
- `sim_fep_pair_fep_minimization_x_g_reduction`
- `sim_fep_pair_markov_blanket_x_precision`
- `sim_fep_pair_surprise_x_generative_model`
- `sim_fep_precision_weighting_probe`
- `sim_fep_surprise_as_distinguishability`
- `sim_fisher_information_classical`
- `sim_geometry_preserving_basis_change_classical`
- `sim_helstrom_guess_bound_classical`
- `sim_history_window_support`
- `sim_holevo_bound_classical`
- `sim_husimi_phase_space_representation_classical`
- `sim_joint_density_matrix_classical`
- `sim_kraus_operator_sum_classical`
- `sim_lego_entropy_relative_js`
- `sim_lego_entropy_shell_history_weighted`
- `sim_lindbladian_evolution_classical`
- `sim_loop_order_family`
- `sim_loop_vector_fields`
- `sim_magic_state_classical`
- `sim_measurement_instrument_classical`
- `sim_min_max_entropy_classical`
- `sim_monogamy_of_entanglement_classical`
- `sim_mutual_information_chain_rule_classical`
- `sim_mutual_information_classical`
- `sim_mutual_information_measure`
- `sim_neg_no_torus_transport`
- `sim_neg_torus_scrambled`
- `sim_operator_coordinate_representation_classical`
- `sim_operator_ordered_entropy`
- `sim_partial_trace_classical`
- `sim_path_entropy`
- `sim_petz_recovery_classical`
- `sim_positivity_constraint`
- `sim_povm_measurement_classical`
- `sim_probe_identity_preservation_classical`
- `sim_purification_classical`
- `sim_quantum_capacity_classical`
- `sim_quantum_discord_classical`
- `sim_quantum_fisher_information_classical`
- `sim_relative_entropy_classical`
- `sim_renyi_entropy_classical`
- `sim_representation_violation_check`
- `sim_resource_theory_of_coherence_classical`
- `sim_ring_checkerboard_support`
- `sim_schmidt_decomposition_classical`
- `sim_schmidt_mode_truncation`
- `sim_shannon_entropy_classical`
- `sim_shell_fuzz_jk`
- `sim_shell_indexed_tensor_network`
- `sim_stabilizer_formalism_classical`
- `sim_strong_subadditivity_classical`
- `sim_syndrome_decoding_classical`
- `sim_torus_seat_entropy`
- `sim_trace_norm_dynamics_classical`
- `sim_unitary_channel_classical`
- `sim_witness_operator_classical`

### bucket 5 off-lane / leviathan (26)

- `sim_leviathan_ai_starvation_under_monoculture|cls=classical_baseline,lb=False`
- `sim_leviathan_as_civilizational_shell_on_manifold|cls=classical_baseline,lb=False`
- `sim_leviathan_atom_2_structure|cls=canonical,lb=False`
- `sim_leviathan_atom_3_reduction|cls=canonical,lb=True`
- `sim_leviathan_atom_4_admissibility|cls=canonical,lb=False`
- `sim_leviathan_atom_5_distinguishability|cls=canonical,lb=True`
- `sim_leviathan_centralization_destroys_admissibility|cls=classical_baseline,lb=False`
- `sim_leviathan_deep_authority_gradient_monotone|cls=canonical,lb=False`
- `sim_leviathan_deep_coalition_minimum_coverage|cls=canonical,lb=False`
- `sim_leviathan_diversity_preserves_fuel_supply|cls=classical_baseline,lb=False`
- `sim_leviathan_explore_as_category_theoretic_pushout|cls=canonical,lb=True`
- `sim_leviathan_explore_as_cellular_automaton|cls=classical_baseline,lb=False`
- `sim_leviathan_explore_as_constraint_satisfaction|cls=canonical,lb=True`
- `sim_leviathan_explore_as_free_energy_landscape|cls=classical_baseline,lb=False`
- `sim_leviathan_explore_as_graph_sheaf|cls=classical_baseline,lb=False`
- `sim_leviathan_explore_as_hypergraph_potential|cls=canonical,lb=True`
- `sim_leviathan_explore_as_information_market|cls=classical_baseline,lb=False`
- `sim_leviathan_explore_as_percolation_network|cls=classical_baseline,lb=False`
- `sim_leviathan_explore_as_replicator_dynamics|cls=classical_baseline,lb=False`
- `sim_leviathan_explore_as_stochastic_process|cls=classical_baseline,lb=False`
- `sim_leviathan_explore_as_topological_data_analysis|cls=canonical,lb=True`
- `sim_leviathan_group_value_divergence_as_distinguishability|cls=classical_baseline,lb=False`
- `sim_leviathan_human_potential_as_wealth_carrier|cls=classical_baseline,lb=False`
- `sim_leviathan_legacy_durability_under_civilizational_reset|cls=classical_baseline,lb=False`
- `sim_leviathan_potential_mining_probe|cls=classical_baseline,lb=False`
- `sim_leviathan_zero_sum_authoritarian_attractor|cls=classical_baseline,lb=False`

### bucket 6 malformed (27)

- `fix_graph_anomalies|cls=None,mf=False`
- `neg_missing_fe_stage_matrix_sim|cls=None,mf=False`
- `neg_missing_operator_stage_matrix_sim|cls=None,mf=False`
- `neg_native_only_stage_matrix_sim|cls=None,mf=False`
- `neg_type_flatten_stage_matrix_sim|cls=None,mf=False`
- `qit_partial_trace|cls=None,mf=False`
- `ratchet_modules|cls=None,mf=False`
- `regenerate_sim_manifest|cls=None,mf=False`
- `sim_classical_constraint_manifold_layers_nested|cls=classical_baseline,mf=False`
- `sim_classical_hopf_fibration_s3_s2|cls=classical_baseline,mf=False`
- `sim_classical_weyl_lr_extraction_projector|cls=classical_baseline,mf=False`
- `sim_loop_vector_fields_classical|cls=classical_baseline,mf=False`
- `sim_low_rank_psd_approximation_classical|cls=classical_baseline,mf=False`
- `sim_operator_low_rank_factorization_classical|cls=classical_baseline,mf=False`
- `sim_placement_law_classical|cls=classical_baseline,mf=False`
- `sim_principal_subspace_classical|cls=classical_baseline,mf=False`
- `sim_qpca_spectral_extraction_classical|cls=classical_baseline,mf=False`
- `sim_schmidt_mode_truncation_classical|cls=classical_baseline,mf=False`
- `sim_signed_operator_variant_classical|cls=classical_baseline,mf=False`
- `sim_spectral_decomposition_classical|cls=classical_baseline,mf=False`
- `sim_spectral_truncation_classical|cls=classical_baseline,mf=False`
- `sim_svd_factorization_classical|cls=classical_baseline,mf=False`
- `sim_terrain_family_fourfold_classical|cls=classical_baseline,mf=False`
- `sim_trace_distance_geometry_classical|cls=classical_baseline,mf=False`
- `source_dirty_stage_plan|cls=None,mf=False`
- `stoch_thermo_core|cls=None,mf=False`
- `telemetry_generator|cls=None,mf=False`

## Lego-backlog candidates (bucket 4, 12)

- `sim_autograd_implicit_diff|cls=canonical`
- `sim_autograd_ntk|cls=canonical`
- `sim_autograd_svd|cls=canonical`
- `sim_fep_atom_1_carrier|cls=canonical`
- `sim_fep_atom_4_admissibility|cls=canonical`
- `sim_fep_deep_active_inference_gradient_flow|cls=canonical`
- `sim_holodeck_atom_5_distinguishability|cls=canonical`
- `sim_holodeck_deep_probe_relative_indistinguishability|cls=canonical`
- `sim_igt_deep_nested_win_lose_irreducibility|cls=canonical`
- `sim_igt_deep_ring_topology_chirality|cls=canonical`
- `sim_sci_method_deep_popper_refutation_unsat_for_tautology|cls=canonical`
- `sim_sci_method_deep_probe_set_determines_falsifiability|cls=canonical`

## Next moves (ordered)

1. Apply bucket 1 → ledger diff (97 ledger-row updates; high-signal work)
2. Append bucket 4 → `queue_lego_backlog.txt` once that file lands live
3. Append bucket 5 → `queue_offlane.txt` once that file lands live
4. Append buckets 3 + 6 → `queue_disposal.txt` with per-row reason comments
5. Retire `queue_default.txt` by renaming to `queue_default.txt.retired_2026_04_19` once sim_runner_v2 is wired. **Do not delete — archive.**
6. Remove `queue_default.txt` from `sim_runner.sh` QUEUES array in the same commit that introduces the new runner.

## Unsupported claims to flag

- Exact DONE count drifts as the runner continues draining live queue. Snapshot count: 243 unique basenames as of ~02:33 local. Bucket totals sum to 252 due to a small number of basenames appearing multiple times as DONE (re-run after edit). Reclassification is per-basename, not per-DONE-line.
- Classifier groups `sim_*_capability` rows under b1 when `load_bearing` is declared. Intended behavior — a capability probe that declares its own tool load-bearing IS a legit ledger-update surface.
- Bucket 6 includes non-probe maintenance scripts (`fix_graph_anomalies`, `regenerate_sim_manifest`, `ratchet_modules`). These should not be in any sim queue; retire them to disposal or move to a separate ops-scripts surface.
