# Capability Triage 2026-06-10

Status: bounded hygiene triage; no git add, no git commit, no sim source edits.

## Scope

- Broad sweep command: `python3 scripts/verify_load_bearing_has_capability_probe.py --report-json`.
- Captured report JSON: `/tmp/capability_triage_report.json`.
- Validator-native report also written by the script: `system_v4/probes/a2_state/sim_results/load_bearing_capability_audit.json`.
- Active v6 lanes excluded from contextual v6 inspection: `stage_lifted_spinor_shell_n5_v0`, `geo_bracketing_smt_lifted_v0`, `geo_network_shell_coordinate_v0`, `geo_s1_coord_state_families_v0`, `geo_s1_q4_finite_incidence_v0`.
- No `system_v4` or `system_v5` sim was rerun or edited.

## Broad Sweep Result

- Audited sims with `TOOL_INTEGRATION_DEPTH`: 3772.
- Current violation count: 319.
- Validator statuses: `probe_stale`=319.

## Cause Classification

| Cause | Count | Disposition |
|---|---:|---|
| `stale-receipt` | 319 | Classify only for legacy v4 estate. Probe files exist, but the expected passing receipt path is absent; do not mass-rerun old estate in this bounded pass. |
| `wrong-env` | 0 | No broad-sweep row classified here. Existing v6 wrong-env-sensitive receipt gates pass. |
| `probe-missing` | 0 | No broad-sweep row classified here. Contextual v6 probe-missing surface is listed separately because creating probes is not a mechanical rerun. |
| `tool-demoted-already` | 0 | No row showed an already-demoted load-bearing declaration in the broad report. |
| `sim-superseded-or-archived` | 0 | No broad-sweep row required this classification; archived v4 lanes were not edited. |

## Broad Sweep Tool Breakdown

| Tool | Stale receipt rows |
|---|---:|
| `numpy` | 193 |
| `pennylane` | 22 |
| `cirq` | 21 |
| `datasketch` | 10 |
| `optuna` | 9 |
| `ribs` | 9 |
| `hdbscan` | 7 |
| `pymoo` | 7 |
| `pynndescent` | 7 |
| `sklearn` | 7 |
| `umap` | 7 |
| `deap` | 6 |
| `evotorch` | 6 |
| `hypothesis` | 5 |
| `networkx` | 3 |

## Mechanical Fixes Applied

None.

Reason: no safe mechanical `system_v6` stale-receipt or wrong-env case was found. Existing v6 Julia capability receipts all pass `summary.all_pass`, their source hash matches `system_v6/probes/julia/julia_load_bearing_capability_probes.jl`, and `project_gate.pass` is true. The S7-relevant `IntervalArithmetic` receipt is already under the required tensorkit project.

## Existing v6 Capability Receipt Health

| Receipt | Tool | all_pass | source_current | project_gate | active_project |
|---|---|---:|---:|---:|---|
| `system_v6/probes/julia/results/cliffordalgebras_capability_results.json` | `CliffordAlgebras` | true | true | true | `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml` |
| `system_v6/probes/julia/results/differentialequations_capability_results.json` | `DifferentialEquations` | true | true | true | `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml` |
| `system_v6/probes/julia/results/intervalarithmetic_capability_results.json` | `IntervalArithmetic` | true | true | true | `/Users/joshuaeisenhart/.julia/environments/codex-ratchet-tensorkit-v1.12/Project.toml` |
| `system_v6/probes/julia/results/quaternions_capability_results.json` | `Quaternions` | true | true | true | `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml` |
| `system_v6/probes/julia/results/symbolics_capability_results.json` | `Symbolics` | true | true | true | `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml` |
| `system_v6/probes/julia/results/z3_capability_results.json` | `Z3` | true | true | true | `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml` |

## Contextual v6 Probe-Missing Surface

- Inspected non-active `system_v6/sims` files with parseable `TOOL_INTEGRATION_DEPTH`: 141.
- Load-bearing declarations lacking an accepted v6 capability receipt in the current v6 capability surface: 220.
- Classification: `probe-missing`, not fixed here. New capability probes or demotion decisions are not mechanical receipt regeneration, and the task explicitly forbids mass editing or sim source edits.

| Tool | v6 probe-missing rows |
|---|---:|
| `cvc5` | 57 |
| `sympy` | 28 |
| `pytorch` | 20 |
| `rustworkx` | 11 |
| `torch_func` | 10 |
| `jax` | 8 |
| `jax_numpy` | 8 |
| `quantumoptics` | 8 |
| `linearalgebra` | 7 |
| `pyg` | 6 |
| `manifolds` | 5 |
| `toponetx` | 5 |
| `gudhi` | 5 |
| `geomstats` | 4 |
| `qutip` | 4 |
| `diffrax` | 4 |
| `xgi` | 4 |
| `quantumclifford` | 3 |
| `e3nn` | 3 |
| `graphs` | 3 |
| `kingdon` | 2 |
| `jax_scipy_linalg` | 2 |
| `quimb` | 2 |
| `e3nn_jax` | 2 |
| `itensors` | 2 |
| `clifford` | 2 |
| `ott` | 1 |
| `galois` | 1 |
| `julia_mod3_stdlib` | 1 |
| `grassmann` | 1 |
| `julia base` | 1 |

## Recommended Disposition

1. Leave the 319 `system_v4/probes` broad-sweep rows classified as legacy stale receipts unless the owner explicitly asks for a targeted old-estate rerun campaign.
2. For `system_v6`, handle `probe_missing` by tool family in small packets: either create one bounded capability probe per load-bearing API surface or demote declarations that are not actually load-bearing. Do not mass-edit sim sources.
3. Preserve the active lane exclusion list above until those lanes are closed or explicitly handed to this hygiene task.
4. Re-run the broad validator after any targeted capability probe rerun and refresh `/tmp/capability_triage_report.json` before claiming improvement.

## Per-Issue Broad Sweep Classification

| Sim file | Tool | Validator status | Cause |
|---|---|---|---|
| `sim_L1_loop_families.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_L3_operators_on_stages.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_L5_axis_orthogonality.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_a0_kernel_discriminator.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_admissibility_manifold_mc.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_axis0_lambda_crosslane_result_audit.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_axis0_lambda_crosslane_result_audit.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_axis0_lambda_crosslane_semantic_bridge.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_axis0_lambda_crosslane_semantic_bridge.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_axis0_lambda_expansion_cosmology_stack.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_axis0_lambda_expansion_cosmology_stack.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_base_loop_law.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_bipartite_entropy_topology_coexistence.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_bipartite_phase_entropy_closure.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_bootstrap_variance_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_branch_weight.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_bridge_family_xi_history.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_bridge_family_xi_point.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_bridge_family_xi_shell.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_bures_geometry.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_capability_datasketch_isolated.py` | `datasketch` | `probe_stale` | `stale-receipt` |
| `sim_capability_deap_isolated.py` | `deap` | `probe_stale` | `stale-receipt` |
| `sim_capability_evotorch_isolated.py` | `evotorch` | `probe_stale` | `stale-receipt` |
| `sim_capability_hdbscan_isolated.py` | `hdbscan` | `probe_stale` | `stale-receipt` |
| `sim_capability_hypothesis_isolated.py` | `hypothesis` | `probe_stale` | `stale-receipt` |
| `sim_capability_optuna_isolated.py` | `optuna` | `probe_stale` | `stale-receipt` |
| `sim_capability_pymoo_isolated.py` | `pymoo` | `probe_stale` | `stale-receipt` |
| `sim_capability_pynndescent_isolated.py` | `pynndescent` | `probe_stale` | `stale-receipt` |
| `sim_capability_ribs_isolated.py` | `ribs` | `probe_stale` | `stale-receipt` |
| `sim_capability_sklearn_isolated.py` | `sklearn` | `probe_stale` | `stale-receipt` |
| `sim_capability_umap_isolated.py` | `umap` | `probe_stale` | `stale-receipt` |
| `sim_carnot_tool_coupling_matrix.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_carnot_two_bath_reversible_cycle.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_carnot_two_bath_reversible_cycle.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_carnot_two_bath_reversible_cycle.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_carrier_probe_support.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_channel_capacity.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_channel_space_geometry.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_characteristic_representation.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_chsh_tsirelson_canonical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_circuit_unitary_canonicalization_z3.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_cirq_matrix_state_bridge.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_cirq_matrix_state_bridge.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_classical_constraint_manifold_layers_nested.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_classical_engine_4operators_kraus.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_classical_hopf_fibration_s3_s2.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_classical_jarzynski_equality_small_system.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_classical_ladder_L0_spectral_baseline.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_classical_ladder_L6_engine_composition.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_classical_maxwell_demon_information_accounting.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_classical_nonclassical_entropy_bridge.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_classical_weyl_lr_extraction_projector.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_clifford_generator_basis.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_coarse_grained_operator_algebra.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_coherence_measure_canonical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_coherent_information_measure.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_commutative_geometry_collapse.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_commutator_algebra.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_compound_equivariant_cayley_gnn.py` | `networkx` | `probe_stale` | `stale-receipt` |
| `sim_concurrence_measure.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_conditional_entropy.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_constraint_manifold_L4_L5_L6.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_constraint_shells_ablation_closure.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_convex_admission_polytope_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_covariance_operator.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_cramer_rao_bound_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_deap_evolve_sim_genome.py` | `deap` | `probe_stale` | `stale-receipt` |
| `sim_density_carrier_dependency_discrimination.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_density_carrier_qutip_qiskit_closure.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_discrete_axis0_field.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_edge_state_writeback.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_em_classical_dark_energy_as_time_pressure.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_em_classical_dark_matter_as_negentropy_reservoir.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_em_classical_entropy_as_space_volume.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_em_classical_fep_mirror_entropy_minimization.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_em_classical_future_compression_future_from_external.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_em_classical_jk_fuzz_as_stochastic_force.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_em_classical_time_as_entropy_increment.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_entanglement_spectrum.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_entanglement_spectrum.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_entanglement_spectrum.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_entropy_family_crosscheck_coexistence.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_entropy_geometry_subordination_probe.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_evotorch_es_constraint_search.py` | `evotorch` | `probe_stale` | `stale-receipt` |
| `sim_evotorch_es_constraint_search.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_f01_finitude_constraint.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_fubini_study_geometry.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_gauge_group_correspondence.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_gauge_group_falsifier_graveyard.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_geometry_preserving_basis_change.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_gerbe_distinguishability_holonomy.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_graph_cell_complex_betti_crosscheck.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_graph_cell_complex_coexistence.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_gudhi_wasserstein_significance.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_hellinger_categorical_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_helstrom_guess_bound.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_hilbert_schmidt_flatness_rejection.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_history_window_entropy.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_history_window_support.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_holevo_bound_canonical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_hopf_deep_linking_number_topology.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_hopf_spinor_density_operator_placement_readout_collision_audit.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_hopf_spinor_density_terrain_loop_dependent_generator_variant_graveyard.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_hopf_spinor_density_terrain_loop_generator_equivalence_audit.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_hopf_spinor_density_time_series_collision_separation_audit.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_hopf_torus_entropy_order_microfit.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_husimi_phase_space_representation.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_hypothesis_property_admissibility_invariant.py` | `hypothesis` | `probe_stale` | `stale-receipt` |
| `sim_igt_holodeck_coupling.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_igt_leviathan_coupling.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_integration_cirq_pennylane_entanglement_bridge.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_integration_cirq_pennylane_entanglement_bridge.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_integration_cirq_qutip_entanglement_bridge.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_integration_classical_nonclassical_entropy_stack.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_integration_datasketch_pyg_lsh_graph.py` | `datasketch` | `probe_stale` | `stale-receipt` |
| `sim_integration_deap_clifford_rotor_evolution.py` | `deap` | `probe_stale` | `stale-receipt` |
| `sim_integration_equivariant_symbolic_graph_manifold_search_stack.py` | `datasketch` | `probe_stale` | `stale-receipt` |
| `sim_integration_equivariant_symbolic_graph_manifold_search_stack.py` | `pynndescent` | `probe_stale` | `stale-receipt` |
| `sim_integration_equivariant_symbolic_graph_manifold_search_stack.py` | `umap` | `probe_stale` | `stale-receipt` |
| `sim_integration_equivariant_symbolic_graph_manifold_search_stack.py` | `hdbscan` | `probe_stale` | `stale-receipt` |
| `sim_integration_equivariant_symbolic_graph_manifold_search_stack.py` | `sklearn` | `probe_stale` | `stale-receipt` |
| `sim_integration_equivariant_symbolic_graph_manifold_search_stack.py` | `optuna` | `probe_stale` | `stale-receipt` |
| `sim_integration_equivariant_symbolic_graph_manifold_search_stack.py` | `pymoo` | `probe_stale` | `stale-receipt` |
| `sim_integration_equivariant_symbolic_graph_manifold_search_stack.py` | `ribs` | `probe_stale` | `stale-receipt` |
| `sim_integration_equivariant_symbolic_graph_manifold_search_stack.py` | `deap` | `probe_stale` | `stale-receipt` |
| `sim_integration_equivariant_symbolic_graph_manifold_search_stack.py` | `evotorch` | `probe_stale` | `stale-receipt` |
| `sim_integration_evotorch_autograd_constraint_search.py` | `evotorch` | `probe_stale` | `stale-receipt` |
| `sim_integration_hdbscan_constraint_clustering.py` | `hdbscan` | `probe_stale` | `stale-receipt` |
| `sim_integration_hypothesis_z3_property_guard.py` | `hypothesis` | `probe_stale` | `stale-receipt` |
| `sim_integration_manifold_cluster_stack.py` | `datasketch` | `probe_stale` | `stale-receipt` |
| `sim_integration_manifold_cluster_stack.py` | `pynndescent` | `probe_stale` | `stale-receipt` |
| `sim_integration_manifold_cluster_stack.py` | `umap` | `probe_stale` | `stale-receipt` |
| `sim_integration_manifold_cluster_stack.py` | `hdbscan` | `probe_stale` | `stale-receipt` |
| `sim_integration_manifold_cluster_stack.py` | `sklearn` | `probe_stale` | `stale-receipt` |
| `sim_integration_manifold_search_archive_stack.py` | `datasketch` | `probe_stale` | `stale-receipt` |
| `sim_integration_manifold_search_archive_stack.py` | `pynndescent` | `probe_stale` | `stale-receipt` |
| `sim_integration_manifold_search_archive_stack.py` | `umap` | `probe_stale` | `stale-receipt` |
| `sim_integration_manifold_search_archive_stack.py` | `hdbscan` | `probe_stale` | `stale-receipt` |
| `sim_integration_manifold_search_archive_stack.py` | `sklearn` | `probe_stale` | `stale-receipt` |
| `sim_integration_manifold_search_archive_stack.py` | `optuna` | `probe_stale` | `stale-receipt` |
| `sim_integration_manifold_search_archive_stack.py` | `ribs` | `probe_stale` | `stale-receipt` |
| `sim_integration_networkx_pyg_graph_roundtrip_micro.py` | `networkx` | `probe_stale` | `stale-receipt` |
| `sim_integration_optuna_sympy_invariant_search.py` | `optuna` | `probe_stale` | `stale-receipt` |
| `sim_integration_pennylane_qutip_entanglement_bridge.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_integration_pymoo_gudhi_pareto_persistence.py` | `pymoo` | `probe_stale` | `stale-receipt` |
| `sim_integration_pynndescent_state_similarity.py` | `pynndescent` | `probe_stale` | `stale-receipt` |
| `sim_integration_quantum_ga_bridge_stack.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_integration_quantum_ga_bridge_stack.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_integration_quantum_ga_bridge_stack.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_integration_quantum_ga_correlator_stack.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_integration_quantum_ga_correlator_stack.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_integration_quantum_open_entangle_correlator_mega_stack.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_integration_quantum_open_entangle_correlator_mega_stack.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_integration_quantum_open_entanglement_stack.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_integration_quantum_open_entanglement_stack.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_integration_ribs_z3_constraint_archive.py` | `ribs` | `probe_stale` | `stale-receipt` |
| `sim_integration_search_archive_stack.py` | `optuna` | `probe_stale` | `stale-receipt` |
| `sim_integration_search_archive_stack.py` | `pymoo` | `probe_stale` | `stale-receipt` |
| `sim_integration_search_archive_stack.py` | `ribs` | `probe_stale` | `stale-receipt` |
| `sim_integration_search_archive_stack.py` | `deap` | `probe_stale` | `stale-receipt` |
| `sim_integration_search_archive_stack.py` | `evotorch` | `probe_stale` | `stale-receipt` |
| `sim_integration_sklearn_shell_clustering.py` | `sklearn` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_search_stack.py` | `datasketch` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_search_stack.py` | `pynndescent` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_search_stack.py` | `umap` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_search_stack.py` | `hdbscan` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_search_stack.py` | `sklearn` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_search_stack.py` | `optuna` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_search_stack.py` | `pymoo` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_search_stack.py` | `ribs` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_search_stack.py` | `deap` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_search_stack.py` | `evotorch` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_stack.py` | `datasketch` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_stack.py` | `pynndescent` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_stack.py` | `umap` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_stack.py` | `hdbscan` | `probe_stale` | `stale-receipt` |
| `sim_integration_symbolic_graph_manifold_stack.py` | `sklearn` | `probe_stale` | `stale-receipt` |
| `sim_integration_thermo_open_system_bridge_stack.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_integration_thermo_open_system_bridge_stack.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_integration_thermo_open_system_bridge_stack.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_integration_umap_gtower_projection.py` | `umap` | `probe_stale` | `stale-receipt` |
| `sim_joint_density_matrix.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_joint_operator_action.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_layer13_19_formal_tools.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_layer4_5_6_formal_tools.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_leggett_garg_k3_canonical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_lego_weyl_geometry_carrier_compare.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_lego_weyl_pauli_transport.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_leviathan_explore_as_hypergraph_potential.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_local_operator_action.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_loop_order_family.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_loop_vector_fields.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_loop_vector_fields_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_low_rank_psd_approximation.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_max_stack_5tool_constraint_admissibility.py` | `hypothesis` | `probe_stale` | `stale-receipt` |
| `sim_max_stack_5tool_constraint_admissibility.py` | `pymoo` | `probe_stale` | `stale-receipt` |
| `sim_max_stack_5tool_constraint_admissibility.py` | `datasketch` | `probe_stale` | `stale-receipt` |
| `sim_max_stack_6tool_gtower_ratchet.py` | `optuna` | `probe_stale` | `stale-receipt` |
| `sim_max_stack_6tool_gtower_ratchet.py` | `ribs` | `probe_stale` | `stale-receipt` |
| `sim_max_stack_constraint_manifold_5tools.py` | `hypothesis` | `probe_stale` | `stale-receipt` |
| `sim_max_stack_constraint_manifold_5tools.py` | `pymoo` | `probe_stale` | `stale-receipt` |
| `sim_max_stack_constraint_manifold_5tools.py` | `datasketch` | `probe_stale` | `stale-receipt` |
| `sim_max_stack_gtower_ratchet_6tools.py` | `optuna` | `probe_stale` | `stale-receipt` |
| `sim_max_stack_gtower_ratchet_6tools.py` | `ribs` | `probe_stale` | `stale-receipt` |
| `sim_measure_feedback_erasure_recovery_cycle_pair.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_measurement_record_reset_parameter_sweep.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_mle_consistency_bernoulli_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_monotone_filtration_convergence_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_mutual_information_measure.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_negativity_measure.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_nested_torus_geometry.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_networkx_hopf_receipt_dependency_reduction.py` | `networkx` | `probe_stale` | `stale-receipt` |
| `sim_neyman_pearson_roc_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_numpy_deep_density_matrix_baseline.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_operator_coordinate_representation.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_operator_geometry_closure_ablation.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_operator_geometry_closure_coexistence.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_operator_geometry_multi_pair_exclusions.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_operator_geometry_shared_state_coexistence.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_operator_geometry_single_pair_exclusion.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_operator_low_rank_factorization.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_operator_ordered_entropy.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_optuna_bayes_search_constraint_threshold.py` | `optuna` | `probe_stale` | `stale-receipt` |
| `sim_path_entropy.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_pauli_algebra_relations.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_pauli_generator_basis.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_placement_law_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_positivity_constraint.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_posterior_concentration_bvm_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_prime_qit_sidecar_graveyard.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_prime_qit_sidecar_probe.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_prime_rosetta_sidecar_fit.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_probe_identity_preservation.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_pure_lego_chiral_overlap.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_pure_lego_density_matrices.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_pure_spinor_transport.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qfi_squeezed_canonical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_closure_companion.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_closure_companion.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_closure_companion.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_finite_time_companion.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_finite_time_companion.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_finite_time_companion.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_hold_policy_companion.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_irreversibility_companion.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_irreversibility_companion.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_irreversibility_companion.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_two_bath_cycle.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_two_bath_cycle.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_qit_carnot_two_bath_cycle.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_qit_moloch_coordination_trap.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_predictive_world_model.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_strong_coupling_landauer.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_strong_coupling_landauer.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_qit_strong_coupling_landauer.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_qit_szilard_bidirectional_protocol.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_szilard_bidirectional_protocol.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_qit_szilard_bidirectional_protocol.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_qit_szilard_landauer_cycle.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_szilard_landauer_cycle.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_qit_szilard_landauer_cycle.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_qit_szilard_record_companion.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_szilard_record_companion.py` | `cirq` | `probe_stale` | `stale-receipt` |
| `sim_qit_szilard_record_companion.py` | `pennylane` | `probe_stale` | `stale-receipt` |
| `sim_qit_szilard_reverse_recovery_companion.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qit_weyl_geometry_companion.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qpca_spectral_extraction.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_qpca_spectral_extraction_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_quantum_discord_canonical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_quantum_metric_nonuniqueness_graveyard.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_real_only_geometry_rejection.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_reduced_state_object.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_relative_entropy_js.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_relative_entropy_nonmetric_boundary.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_representation_violation_check.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_ribs_map_elites_constraint_manifold_archive.py` | `ribs` | `probe_stale` | `stale-receipt` |
| `sim_ring_checkerboard_support.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_rosetta_detector_minhash.py` | `datasketch` | `probe_stale` | `stale-receipt` |
| `sim_rosetta_lego_coupled_array.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_rosetta_lego_coupled_array_graveyard.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_rosetta_triad_entropy_topology_sweep.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_rosetta_triad_modes.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_rosetta_triad_order_graveyard.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_schmidt_decomposition.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_schmidt_mode_truncation.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_schmidt_mode_truncation_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_sequential_admission_wald_boundaries_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_shannon_entropy.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_shell_fuzz_jk.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_shell_indexed_tensor_network.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_shell_weighted_entropy_field.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_shell_window_support.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_six_bit_gray_code_single_flip_cycle_invariant.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_spectral_triple_carrier_algebra.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_spectral_triple_chirality_gamma_grading.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_spectral_triple_dirac_spectrum.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_spectral_triple_distinguishability_heat_trace.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_spectral_triple_reduction_connes_distance.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_spectral_truncation.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_spectral_truncation_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_sphere_geometry.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_sprt_wald_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_stokes_parameterization.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_sufficient_statistics_expfam_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_superdense_coding_capacity_canonical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_svd_factorization.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_szilard_record_ordering_refinement_measurement_accuracy_recheck.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_szilard_record_ordering_refinement_reset_swing_sweep.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_terrain_family_fourfold_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_three_qubit_coherent_information_register.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_torus_seat_entropy.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_trace_distance_geometry.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_trace_distance_geometry_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_transport_weighted_entropy.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_tv_contraction_dpi_classical.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_two_bath_heat_work_reversible_cycle_pair.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_unsigned_entropy_family.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_viability_vs_attractor.py` | `numpy` | `probe_stale` | `stale-receipt` |
| `sim_von_neumann_entropy.py` | `numpy` | `probe_stale` | `stale-receipt` |

## RECONCILIATION Addendum: v6 Surface Metric vs Per-Sim Verifier

Date: 2026-06-10.

Verdict: mixed.

The 220-row contextual v6 metric is real only under the stricter "current v6 capability surface" criterion. It is not the same criterion enforced by `scripts/verify_load_bearing_has_capability_probe.py --sim`.

Mechanism:

- The contextual v6 scan accepts only current v6 capability receipts under `system_v6/probes/julia/results/*_capability_results.json` with `summary.all_pass == true` and `project_gate.pass == true`.
- The per-sim verifier script still consults the legacy capability surface:
  - probes: `system_v4/probes/sim_<tool>_capability.py` or `system_v4/probes/sim_capability_<tool>_isolated.py`
  - results: `system_v4/probes/a2_state/sim_results/<tool>_capability_results.json` or `system_v4/probes/a2_state/sim_results/sim_capability_<tool>_isolated_results.json`
  - accepted result fields: `summary.all_pass == true`, or top-level `overall_pass == true`, or top-level `passed == true`
- Therefore a v6 sim can be flagged by the 220 metric while still passing the existing per-sim verifier for the same tool, because the verifier treats a legacy v4 receipt as sufficient.

Reconstructed contextual v6 scan:

- Active lane dirs excluded: `stage_lifted_spinor_shell_n5_v0`, `geo_bracketing_smt_lifted_v0`, `geo_network_shell_coordinate_v0`, `geo_s1_coord_state_families_v0`, `geo_s1_q4_finite_incidence_v0`.
- Parseable non-active `system_v6/sims` files with `TOOL_INTEGRATION_DEPTH`: 141.
- Rows lacking an accepted current v6 receipt: 220 across 90 sim files.
- Accepted current v6 tools found: `cliffordalgebras`, `differentialequations`, `intervalarithmetic`, `quaternions`, `symbolics`, `z3`.

Split of the 220 rows:

| Class | Count | Meaning |
|---|---:|---|
| v6-surface gap but legacy verifier OK | 177 | Not a current `verify_load_bearing_has_capability_probe.py` defect. These rows pass because the script finds accepted legacy `system_v4/probes` receipts. |
| gap under both surfaces | 43 | These rows lack an accepted current v6 receipt and also lack an accepted receipt under the verifier's legacy lookup. |

Sampled per-sim verifier gates, run now with `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`:

| Sample row tool | Sim | Verifier exit | Row status in verifier | Notes |
|---|---|---:|---|---|
| `cvc5` | `system_v6/sims/assoc_weakening_lattice_classifier/assoc_weakening_lattice_classifier_jax.py` | 1 | `ok` | Sim fails on `jax` and `jax_numpy`, not on sampled `cvc5`. |
| `sympy` | `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_jax.py` | 1 | `ok` | Sim fails on `ott`, not on sampled `sympy`. |
| `pytorch` | `system_v6/sims/assoc_weakening_lattice_classifier/assoc_weakening_lattice_classifier_pytorch.py` | 1 | `ok` | Sim fails on `torch_func`, not on sampled `pytorch`. |
| `rustworkx` | `system_v6/sims/geo_s1_five_qubit_safety_margin_exact_v0/geo_s1_five_qubit_safety_margin_exact_v0_jax.py` | 0 | `ok` | All load-bearing tools in this sim pass the legacy verifier. |
| `torch_func` | `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_pytorch.py` | 1 | `missing_probe` | Missing under both surfaces. |
| `jax` | `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_jax.py` | 1 | `missing_probe` | Missing under both surfaces. |
| `pyg` | `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_pytorch.py` | 0 | `ok` | All load-bearing tools in this sim pass the legacy verifier. |
| `gudhi` | `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_jax.py` | 0 | `ok` | All load-bearing tools in this sim pass the legacy verifier. |

Rows missing under both surfaces:

| Sim file | Declared tool | Canonical tool |
|---|---|---|
| `system_v6/sims/assoc_weakening_lattice_classifier/assoc_weakening_lattice_classifier_jax.py` | `jax` | `jax` |
| `system_v6/sims/assoc_weakening_lattice_classifier/assoc_weakening_lattice_classifier_jax.py` | `jax.numpy` | `jax_numpy` |
| `system_v6/sims/assoc_weakening_lattice_classifier/assoc_weakening_lattice_classifier_pytorch.py` | `torch.func` | `torch_func` |
| `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_jax.py` | `jax` | `jax` |
| `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_jax.py` | `jax.numpy` | `jax_numpy` |
| `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_julia.jl` | `LinearAlgebra` | `linearalgebra` |
| `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_pytorch.py` | `torch.func` | `torch_func` |
| `system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_julia.jl` | `LinearAlgebra` | `linearalgebra` |
| `system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/dual_stack_carnot_szilard_hopf_weyl_probe_jax.py` | `jax` | `jax` |
| `system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/dual_stack_carnot_szilard_hopf_weyl_probe_jax.py` | `jax.numpy` | `jax_numpy` |
| `system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py` | `torch.func` | `torch_func` |
| `system_v6/sims/flux_emergence_discriminator/flux_emergence_discriminator_pytorch.py` | `torch.func` | `torch_func` |
| `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_jax.py` | `ott` | `ott` |
| `system_v6/sims/geo_s1_finite_phase_lens_v0/geo_s1_finite_phase_lens_v0_pytorch.py` | `torch.func` | `torch_func` |
| `system_v6/sims/geo_s1_q3_finite_incidence_v0/geo_s1_q3_finite_incidence_v0_jax.py` | `galois` | `galois` |
| `system_v6/sims/geo_s1_q3_finite_incidence_v0/geo_s1_q3_finite_incidence_v0_julia.jl` | `julia_mod3_stdlib` | `julia_mod3_stdlib` |
| `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_pytorch.py` | `torch.func` | `torch_func` |
| `system_v6/sims/geo_s1_spinor_hopf_free_v0/geo_s1_spinor_hopf_free_v0_pytorch.py` | `torch.func` | `torch_func` |
| `system_v6/sims/geo_s2_connection_flux_foliation_v0/geo_s2_connection_flux_foliation_v0_julia.jl` | `Grassmann` | `grassmann` |
| `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_jax.py` | `jax` | `jax` |
| `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_jax.py` | `jax.numpy` | `jax_numpy` |
| `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_jax.py` | `jax.scipy.linalg` | `jax_scipy_linalg` |
| `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl` | `LinearAlgebra` | `linearalgebra` |
| `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl` | `Graphs` | `graphs` |
| `system_v6/sims/mct_nonassoc_weld_packet_v0/mct_nonassoc_weld_packet_v0_julia.jl` | `LinearAlgebra` | `linearalgebra` |
| `system_v6/sims/nesting_consistency_family_v0/nesting_consistency_family_v0_pytorch.py` | `torch.func` | `torch_func` |
| `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_jax.py` | `jax` | `jax` |
| `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_jax.py` | `jax.numpy` | `jax_numpy` |
| `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_julia.jl` | `Graphs` | `graphs` |
| `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_julia.jl` | `LinearAlgebra` | `linearalgebra` |
| `system_v6/sims/source_locked_operator_base_packet/source_locked_operator_base_packet_pytorch.py` | `torch.func` | `torch_func` |
| `system_v6/sims/spinor_network_hopf_weyl_testbed/spinor_network_hopf_weyl_testbed_julia.jl` | `Graphs` | `graphs` |
| `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py` | `jax` | `jax` |
| `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py` | `jax.numpy` | `jax_numpy` |
| `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py` | `jax.scipy.linalg` | `jax_scipy_linalg` |
| `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_julia.jl` | `LinearAlgebra` | `linearalgebra` |
| `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_pytorch.py` | `torch.func` | `torch_func` |
| `system_v6/sims/terrain_operator_precedence_64_matrix/terrain_operator_precedence_64_matrix_jax.py` | `jax` | `jax` |
| `system_v6/sims/terrain_operator_precedence_64_matrix/terrain_operator_precedence_64_matrix_jax.py` | `jax.numpy` | `jax_numpy` |
| `system_v6/sims/terrain_operator_precedence_64_matrix/terrain_operator_precedence_64_matrix_julia.jl` | `LinearAlgebra` | `linearalgebra` |
| `system_v6/sims/winlose_pattern_derivation_discriminator/winlose_pattern_derivation_discriminator_jax.py` | `jax` | `jax` |
| `system_v6/sims/winlose_pattern_derivation_discriminator/winlose_pattern_derivation_discriminator_jax.py` | `jax.numpy` | `jax_numpy` |
| `system_v6/sims/winlose_pattern_derivation_discriminator/winlose_pattern_derivation_discriminator_julia.jl` | `Julia Base` | `julia base` |

Operational reading:

- Do not treat all 220 rows as current verifier defects.
- Do treat all 220 rows as a strict current-v6-surface incompleteness metric if v6 capability receipts are now required.
- The honest defect count against the script that builders actually passed is 43 rows, not 220.
- The honest migration gap from legacy accepted receipts to current v6 receipts is 177 rows.

No probes were created, no sim files were edited, and no git staging or commit was performed for this reconciliation.

## DISPOSITION Addendum: 43 Both-Surface Capability Gaps

Scope: exactly the 43 rows in the RECONCILIATION addendum table above. No other sim rows were dispositioned. No active-lane sims were edited (`stage_lifted_spinor_shell_n5_v0`, `geo_network_shell_coordinate_v0`, `geo_s1_coord_state_families_v0`, `geo_s1_q4_finite_incidence_v0`, `geo_bracketing_smt_lifted_v0`). No `git add` or `git commit` was performed.

Criterion applied: `load_bearing` requires a passing capability probe under `scripts/verify_load_bearing_has_capability_probe.py` and lint C5. Bare engine substrates (`jax`, `jax.numpy`, local Julia stdlib/substrate entries) were not treated as load-bearing tools.

Probe receipts generated fresh by running the capability probes:

| Canonical tool | Probe source | Receipt consulted by verifier | Probe exit |
|---|---|---|---:|
| `torch_func` | `system_v4/probes/sim_torch_func_capability.py` | `system_v4/probes/a2_state/sim_results/torch_func_capability_results.json` | 0 |
| `ott` | `system_v4/probes/sim_ott_capability.py` | `system_v4/probes/a2_state/sim_results/ott_capability_results.json` | 0 |
| `galois` | `system_v4/probes/sim_galois_capability.py` | `system_v4/probes/a2_state/sim_results/galois_capability_results.json` | 0 |
| `jax_scipy_linalg` | `system_v4/probes/sim_jax_scipy_linalg_capability.py` | `system_v4/probes/a2_state/sim_results/jax_scipy_linalg_capability_results.json` | 0 |
| `graphs` | `system_v4/probes/sim_graphs_capability.py` | `system_v4/probes/a2_state/sim_results/graphs_capability_results.json` | 0 |
| `grassmann` | `system_v4/probes/sim_grassmann_capability.py` | `system_v4/probes/a2_state/sim_results/grassmann_capability_results.json` | 0 |

Disposition legend: `a` = substrate/local misdeclaration demoted to supportive; `b` = rich tool with real gating work retained as load-bearing after a fresh capability probe receipt; `c` = genuinely decorative. No row required `c`.

| # | Sim file | Tool | Canonical | Disposition | Action | Verifier before -> after |
|---:|---|---|---|---|---|---|
| 1 | `system_v6/sims/assoc_weakening_lattice_classifier/assoc_weakening_lattice_classifier_jax.py` | `jax` | `jax` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 2 | `system_v6/sims/assoc_weakening_lattice_classifier/assoc_weakening_lattice_classifier_jax.py` | `jax.numpy` | `jax_numpy` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 3 | `system_v6/sims/assoc_weakening_lattice_classifier/assoc_weakening_lattice_classifier_pytorch.py` | `torch.func` | `torch_func` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 4 | `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_jax.py` | `jax` | `jax` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 5 | `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_jax.py` | `jax.numpy` | `jax_numpy` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 6 | `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_julia.jl` | `LinearAlgebra` | `linearalgebra` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 7 | `system_v6/sims/axis_independence_discriminators_036/axis_independence_discriminators_036_pytorch.py` | `torch.func` | `torch_func` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 8 | `system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_julia.jl` | `LinearAlgebra` | `linearalgebra` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 9 | `system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/dual_stack_carnot_szilard_hopf_weyl_probe_jax.py` | `jax` | `jax` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 10 | `system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/dual_stack_carnot_szilard_hopf_weyl_probe_jax.py` | `jax.numpy` | `jax_numpy` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 11 | `system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py` | `torch.func` | `torch_func` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 12 | `system_v6/sims/flux_emergence_discriminator/flux_emergence_discriminator_pytorch.py` | `torch.func` | `torch_func` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 13 | `system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_jax.py` | `ott` | `ott` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 14 | `system_v6/sims/geo_s1_finite_phase_lens_v0/geo_s1_finite_phase_lens_v0_pytorch.py` | `torch.func` | `torch_func` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 15 | `system_v6/sims/geo_s1_q3_finite_incidence_v0/geo_s1_q3_finite_incidence_v0_jax.py` | `galois` | `galois` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 16 | `system_v6/sims/geo_s1_q3_finite_incidence_v0/geo_s1_q3_finite_incidence_v0_julia.jl` | `julia_mod3_stdlib` | `julia_mod3_stdlib` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 17 | `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_pytorch.py` | `torch.func` | `torch_func` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 18 | `system_v6/sims/geo_s1_spinor_hopf_free_v0/geo_s1_spinor_hopf_free_v0_pytorch.py` | `torch.func` | `torch_func` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 19 | `system_v6/sims/geo_s2_connection_flux_foliation_v0/geo_s2_connection_flux_foliation_v0_julia.jl` | `Grassmann` | `grassmann` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 20 | `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_jax.py` | `jax` | `jax` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 21 | `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_jax.py` | `jax.numpy` | `jax_numpy` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 22 | `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_jax.py` | `jax.scipy.linalg` | `jax_scipy_linalg` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 23 | `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl` | `LinearAlgebra` | `linearalgebra` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 24 | `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl` | `Graphs` | `graphs` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 25 | `system_v6/sims/mct_nonassoc_weld_packet_v0/mct_nonassoc_weld_packet_v0_julia.jl` | `LinearAlgebra` | `linearalgebra` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 26 | `system_v6/sims/nesting_consistency_family_v0/nesting_consistency_family_v0_pytorch.py` | `torch.func` | `torch_func` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 27 | `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_jax.py` | `jax` | `jax` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 28 | `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_jax.py` | `jax.numpy` | `jax_numpy` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 29 | `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_julia.jl` | `Graphs` | `graphs` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 30 | `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_julia.jl` | `LinearAlgebra` | `linearalgebra` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 31 | `system_v6/sims/source_locked_operator_base_packet/source_locked_operator_base_packet_pytorch.py` | `torch.func` | `torch_func` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 32 | `system_v6/sims/spinor_network_hopf_weyl_testbed/spinor_network_hopf_weyl_testbed_julia.jl` | `Graphs` | `graphs` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 33 | `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py` | `jax` | `jax` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 34 | `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py` | `jax.numpy` | `jax_numpy` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 35 | `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py` | `jax.scipy.linalg` | `jax_scipy_linalg` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 36 | `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_julia.jl` | `LinearAlgebra` | `linearalgebra` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 37 | `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_pytorch.py` | `torch.func` | `torch_func` | `b` | Fresh capability probe receipt generated; load-bearing retained. | 1 -> 0 |
| 38 | `system_v6/sims/terrain_operator_precedence_64_matrix/terrain_operator_precedence_64_matrix_jax.py` | `jax` | `jax` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 39 | `system_v6/sims/terrain_operator_precedence_64_matrix/terrain_operator_precedence_64_matrix_jax.py` | `jax.numpy` | `jax_numpy` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 40 | `system_v6/sims/terrain_operator_precedence_64_matrix/terrain_operator_precedence_64_matrix_julia.jl` | `LinearAlgebra` | `linearalgebra` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 41 | `system_v6/sims/winlose_pattern_derivation_discriminator/winlose_pattern_derivation_discriminator_jax.py` | `jax` | `jax` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 42 | `system_v6/sims/winlose_pattern_derivation_discriminator/winlose_pattern_derivation_discriminator_jax.py` | `jax.numpy` | `jax_numpy` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |
| 43 | `system_v6/sims/winlose_pattern_derivation_discriminator/winlose_pattern_derivation_discriminator_julia.jl` | `Julia Base` | `julia base` | `a` | Demoted to supportive; affected leg and envelope rerun. | 1 -> 0 |

Rerun and validation receipts:

| Check | Scope | Exit/result |
|---|---|---|
| Full affected leg/envelope rerun | demoted source rows in `assoc_weakening_lattice_classifier`, `axis_independence_discriminators_036`, `bloch_root_admissibility_discriminator_v0`, `dual_stack_carnot_szilard_hopf_weyl_probe`, `geo_s1_q3_finite_incidence_v0`, `mct_dynamic_admissibility_packet_v0`, `mct_nonassoc_weld_packet_v0`, `ring_checkerboard_support_graph_probe`, `terrain_generator_sheet_packet`, `terrain_operator_precedence_64_matrix`, `winlose_pattern_derivation_discriminator` | all rerun commands exit 0 |
| `scripts/verify_load_bearing_has_capability_probe.py --sim ...` | 31 unique sim files represented by the 43 rows | all exit 0 |
| `scripts/lint_sim_contract.py ...` | 20 Python sim files represented by the 43 rows | exit 0; `violation_total: 0` |
| `scripts/validate_three_engine_sim_result.py ...` | 11 rerun envelope JSONs | all exit 0; each emitted `ok: true` |

Claim stability: committed envelope claim values remained exact-class stable. The envelope-level `classification`, `promotion_allowed`, `divergence`, and `crossover_proofs` fields matched `HEAD` for the rerun envelopes. Differences were limited to capability/tool-surface metadata and the intended removal of demoted substrate/local entries from `claim_path_tools`; exact/probe rows that only needed new capability receipts did not have their sim result surfaces rerun or changed.
