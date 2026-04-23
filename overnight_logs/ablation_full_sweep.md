# Ablation Full Sweep Report

- Total sims swept: 86
- Sims with no load_bearing declared: 7
- Baseline-fail sims: 11
- Irreducible (sim,tool) pairs: 86
- Decorative (sim,tool) pairs: 0
- Total load-bearing claims tested: 99
- Irreducibility rate: 86/99 = 86.9%

## sim × tool × status

| sim | tool | status |
|---|---|---|
| sim_autograd_deep_entropy_monotone_under_cptp.py | pytorch | irreducible |
| sim_autograd_deep_fisher_information_eigvals.py | pytorch | irreducible |
| sim_autograd_deep_hessian_psd_at_admissible_point.py | pytorch | irreducible |
| sim_autograd_deep_implicit_function_theorem_constraint.py | pytorch | irreducible |
| sim_autograd_deep_jacobian_rank_distinguishability.py | pytorch | irreducible |
| sim_autograd_deep_kl_divergence_gradient.py | pytorch | irreducible |
| sim_autograd_deep_nabla_Ic_admissibility.py | pytorch | irreducible |
| sim_autograd_deep_second_order_couple_to_axis0.py | pytorch | irreducible |
| sim_axis0_chiral_deep_search.py | None | no_load_bearing_declared |
| sim_axis7_deep_test.py | None | no_load_bearing_declared |
| sim_clifford_deep_cl3_rotor_double_cover.py | clifford | irreducible |
| sim_compound_autograd_sympy_z3_fisher_admissibility.py | pytorch | irreducible |
| sim_compound_autograd_sympy_z3_fisher_admissibility.py | sympy | irreducible |
| sim_compound_autograd_sympy_z3_fisher_admissibility.py | z3 | irreducible |
| sim_compound_autograd_topo_mp.py | None | no_load_bearing_declared |
| sim_compound_clifford_e3nn_so3_equivariance.py | clifford | irreducible |
| sim_compound_clifford_e3nn_so3_equivariance.py | e3nn | irreducible |
| sim_compound_clifford_pytorch_xgi_higher_order_rotor.py | pytorch | irreducible |
| sim_compound_clifford_pytorch_xgi_higher_order_rotor.py | clifford | irreducible |
| sim_compound_clifford_pytorch_xgi_higher_order_rotor.py | xgi | irreducible |
| sim_compound_cvc5_rustworkx_toponetx_graph_topology.py | cvc5 | irreducible |
| sim_compound_cvc5_rustworkx_toponetx_graph_topology.py | rustworkx | irreducible |
| sim_compound_cvc5_rustworkx_toponetx_graph_topology.py | toponetx | irreducible |
| sim_compound_dual_solver_bc_fence.py | None | no_load_bearing_declared |
| sim_compound_equivariant_cayley_gnn.py | None | no_load_bearing_declared |
| sim_compound_legos_forced.py | None | no_load_bearing_declared |
| sim_compound_operator_geometry.py | clifford | baseline_fail |
| sim_compound_pyg_autograd_hopf_ratchet.py | pyg | irreducible |
| sim_compound_pyg_autograd_hopf_ratchet.py | pytorch | irreducible |
| sim_compound_pyg_toponetx_gudhi_hodge_pipeline.py | pyg | irreducible |
| sim_compound_pyg_toponetx_gudhi_hodge_pipeline.py | toponetx | irreducible |
| sim_compound_pyg_toponetx_gudhi_hodge_pipeline.py | gudhi | irreducible |
| sim_compound_torus_spinor_admissibility.py | None | no_load_bearing_declared |
| sim_compound_torus_spinor_admissibility_cvc5_parity.py | cvc5 | irreducible |
| sim_compound_z3_clifford_e3nn_so3_chirality.py | clifford | irreducible |
| sim_compound_z3_clifford_e3nn_so3_chirality.py | e3nn | irreducible |
| sim_compound_z3_clifford_e3nn_so3_chirality.py | z3 | irreducible |
| sim_compound_z3_clifford_pyg_so3_admissibility.py | pyg | baseline_fail |
| sim_compound_z3_clifford_pyg_so3_admissibility.py | z3 | baseline_fail |
| sim_compound_z3_clifford_pyg_so3_admissibility.py | clifford | baseline_fail |
| sim_compound_z3_cvc5_kcbs_parity.py | z3 | irreducible |
| sim_compound_z3_cvc5_kcbs_parity.py | cvc5 | irreducible |
| sim_compound_z3_sympy_clifford_bch_unsat.py | z3 | irreducible |
| sim_compound_z3_sympy_clifford_bch_unsat.py | sympy | irreducible |
| sim_compound_z3_sympy_clifford_bch_unsat.py | clifford | irreducible |
| sim_cvc5_deep_bc04_identity_fence.py | cvc5 | irreducible |
| sim_cvc5_deep_bc05_identity_fence_sibling.py | cvc5 | irreducible |
| sim_cvc5_deep_bv_forbidden_placement.py | cvc5 | irreducible |
| sim_cvc5_deep_chsh_nolhv.py | cvc5 | irreducible |
| sim_cvc5_deep_nra_primitive_root_unity.py | cvc5 | irreducible |
| sim_cvc5_deep_strings_carrier_labels.py | cvc5 | irreducible |
| sim_cvc5_deep_z3_cvc5_agreement.py | cvc5 | irreducible |
| sim_cvc5_deep_z3_cvc5_agreement.py | z3 | irreducible |
| sim_e3nn_deep_hopf_cg.py | e3nn | irreducible |
| sim_f01_deep_01_probe_size_lower_bound_log2_N.py | z3 | baseline_fail |
| sim_f01_deep_02_finiteness_forces_discrete_spectrum.py | sympy | baseline_fail |
| sim_f01_deep_03_information_bound_shannon_log_N_max.py | sympy | baseline_fail |
| sim_f01_deep_04_distinguishability_quantum_nonzero.py | z3 | baseline_fail |
| sim_f01_deep_05_probe_reuse_compresses_capacity.py | sympy | baseline_fail |
| sim_geomstats_deep_frechet_mean_convergence.py | geomstats | irreducible |
| sim_geomstats_deep_grassmannian_distinguishability.py | geomstats | irreducible |
| sim_geomstats_deep_hyperbolic_parallel_transport.py | geomstats | irreducible |
| sim_geomstats_deep_lie_group_bch_agreement.py | geomstats | irreducible |
| sim_geomstats_deep_s2_frechet.py | geomstats | irreducible |
| sim_geomstats_deep_so3_exp_log_consistency.py | geomstats | irreducible |
| sim_geomstats_deep_spd_affine_invariant_metric.py | geomstats | irreducible |
| sim_geomstats_deep_sphere_geodesic_admissibility.py | geomstats | irreducible |
| sim_geomstats_deep_stiefel_orthogonality_excludes.py | geomstats | irreducible |
| sim_gudhi_deep_persistence_diagram_stability_under_probe.py | gudhi | irreducible |
| sim_gudhi_deep_persistent_h1_excludes_trivial_homology.py | gudhi | irreducible |
| sim_gudhi_deep_rips_vs_cech_admissibility.py | gudhi | irreducible |
| sim_gudhi_deep_s3_hopf_torus_persistent_homology.py | gudhi | baseline_fail |
| sim_n01_deep_equality_is_not_primitive.py | sympy | irreducible |
| sim_n01_deep_equality_is_not_primitive.py | z3 | irreducible |
| sim_n01_deep_identity_forces_equivalence_classes.py | sympy | irreducible |
| sim_n01_deep_indistinguishability_is_transitive.py | z3 | irreducible |
| sim_n01_deep_probe_set_determines_ontology.py | z3 | irreducible |
| sim_n01_deep_universals_reduce_to_particulars.py | z3 | irreducible |
| sim_networkx_deep_expander_gap.py | networkx | irreducible |
| sim_numpy_deep_density_matrix_baseline.py | numpy | irreducible |
| sim_pyg_deep_hopf_u1_equivariant_conservation.py | pytorch | irreducible |
| sim_pyg_deep_oversmoothing_bound.py | pyg | irreducible |
| sim_rustworkx_deep_bfs_layer_distinguishability.py | rustworkx | irreducible |
| sim_rustworkx_deep_bipartite_exclusion.py | rustworkx | irreducible |
| sim_rustworkx_deep_cayley_s4_admissibility.py | rustworkx | irreducible |
| sim_rustworkx_deep_cycle_basis_generator.py | rustworkx | irreducible |
| sim_rustworkx_deep_isomorphism_class_excludes.py | rustworkx | irreducible |
| sim_rustworkx_deep_mincut_probe_relative.py | rustworkx | irreducible |
| sim_rustworkx_deep_pagerank_admissibility_bound.py | rustworkx | irreducible |
| sim_rustworkx_deep_planarity_vs_genus.py | rustworkx | irreducible |
| sim_rustworkx_deep_scc_admissibility.py | rustworkx | irreducible |
| sim_sympy_deep_lindblad_dephasing_spectrum.py | sympy | baseline_fail |
| sim_toponetx_deep_cell_complex_boundary_consistency.py | toponetx | irreducible |
| sim_toponetx_deep_hodge_boundary.py | toponetx | baseline_fail |
| sim_toponetx_deep_hodge_kernel_admissibility.py | toponetx | irreducible |
| sim_toponetx_deep_hodge_laplacian_kernel_excludes_nontrivial.py | toponetx | irreducible |
| sim_toponetx_deep_simplicial_vs_cell_distinguishability.py | toponetx | irreducible |
| sim_torch_deep_axis0_autograd_vn_entropy.py | pytorch | baseline_fail |
| sim_xgi_deep_higher_order_contagion.py | xgi | irreducible |
| sim_xgi_deep_hyperedge_motif_count.py | xgi | irreducible |
| sim_xgi_deep_hypergraph_clustering.py | xgi | irreducible |
| sim_xgi_deep_hyperlap_triadic_vs_pairwise.py | xgi | irreducible |
| sim_xgi_deep_leviathan_hyperlap.py | xgi | irreducible |
| sim_xgi_deep_toponetx_hodge_agreement.py | xgi | irreducible |
| sim_xgi_deep_toponetx_hodge_agreement.py | toponetx | irreducible |
| sim_z3_deep_no_classical_stochastic_under_dephasing_weyl_commute.py | z3 | irreducible |

## Decorative tool claims (flag)

## Baseline failures (flag)
- system_v4/probes/sim_compound_operator_geometry.py
- system_v4/probes/sim_compound_z3_clifford_pyg_so3_admissibility.py
- system_v4/probes/sim_f01_deep_01_probe_size_lower_bound_log2_N.py
- system_v4/probes/sim_f01_deep_02_finiteness_forces_discrete_spectrum.py
- system_v4/probes/sim_f01_deep_03_information_bound_shannon_log_N_max.py
- system_v4/probes/sim_f01_deep_04_distinguishability_quantum_nonzero.py
- system_v4/probes/sim_f01_deep_05_probe_reuse_compresses_capacity.py
- system_v4/probes/sim_gudhi_deep_s3_hopf_torus_persistent_homology.py
- system_v4/probes/sim_sympy_deep_lindblad_dephasing_spectrum.py
- system_v4/probes/sim_toponetx_deep_hodge_boundary.py
- system_v4/probes/sim_torch_deep_axis0_autograd_vn_entropy.py

## No load_bearing declared
- system_v4/probes/sim_axis0_chiral_deep_search.py
- system_v4/probes/sim_axis7_deep_test.py
- system_v4/probes/sim_compound_autograd_topo_mp.py
- system_v4/probes/sim_compound_dual_solver_bc_fence.py
- system_v4/probes/sim_compound_equivariant_cayley_gnn.py
- system_v4/probes/sim_compound_legos_forced.py
- system_v4/probes/sim_compound_torus_spinor_admissibility.py