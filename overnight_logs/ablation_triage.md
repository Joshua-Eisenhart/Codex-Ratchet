# Ablation Triage

- HIGH total: 223
- HIGH canonical: 219
- HIGH non-canonical: 4
- Summary: {'HIGH': 223, 'LOW': 57, 'MEDIUM': 27}

## Canonical HIGH (flagged — review priority)

### pytorch (79)
- `system_v4/probes/sim_3qubit_bridge_prototype.py` — reason: load_bearing: d=8 density-matrix algebra, partial-trace reductions, and coherent-information evaluat
- `system_v4/probes/sim_SA5_curvature_commutator.py` — reason: 
- `system_v4/probes/sim_axis6_canonical.py` — reason: 
- `system_v4/probes/sim_axis6_entropy_decomposition.py` — reason: 
- `system_v4/probes/sim_axis6_rank_coherence.py` — reason: 
- `system_v4/probes/sim_axis7_12_gs_residual_axes.py` — reason: 
- `system_v4/probes/sim_axis7_12_orthogonal_closure.py` — reason: 
- `system_v4/probes/sim_berry_qfi_entangled_path.py` — reason: 
- `system_v4/probes/sim_berry_qfi_shell_paths.py` — reason: 
- `system_v4/probes/sim_blp_non_markovianity_canonical.py` — reason: 
- `system_v4/probes/sim_bridge_chain_integration.py` — reason: 
- `system_v4/probes/sim_bridge_fe_relay_sweep.py` — reason: 
- `system_v4/probes/sim_bridge_to_rhoab_construction.py` — reason: 
- `system_v4/probes/sim_chsh_tsirelson_canonical.py` — reason: placeholder -- filled below
- `system_v4/probes/sim_coherence_measure_canonical.py` — reason: 
- `system_v4/probes/sim_coherent_info_erasure_canonical.py` — reason: 
- `system_v4/probes/sim_constraint_shells_binding_crosscheck.py` — reason: 
- `system_v4/probes/sim_density_hopf_geometry.py` — reason: 
- `system_v4/probes/sim_dissipative_kraus_shell_compatibility.py` — reason: 
- `system_v4/probes/sim_e3nn_hopf_spinor_equivariance.py` — reason: all tensor ops, SU(2) matrices, density matrices
- `system_v4/probes/sim_e3nn_ic_invariance.py` — reason: density matrix ops, partial trace, entropy, SU(2) unitaries
- `system_v4/probes/sim_e3nn_relay_equivariance.py` — reason: XX gate as matrix, Bloch vector extraction, density matrices
- `system_v4/probes/sim_e3nn_tensor_product.py` — reason: all tensor ops, density matrices, von Neumann entropy
- `system_v4/probes/sim_entanglement_breaking_ppt_witness_canonical.py` — reason: 
- `system_v4/probes/sim_foundation_pauli_bloch_backprop.py` — reason: 
- `system_v4/probes/sim_geometric_constraint_manifold_pyg.py` — reason: 
- `system_v4/probes/sim_geomstats_ratchet_trajectory.py` — reason: 
- `system_v4/probes/sim_ghz_mermin_inequality_canonical.py` — reason: 
- `system_v4/probes/sim_gudhi_bipartite_entangled.py` — reason: 
- `system_v4/probes/sim_gudhi_phase_sensitive_kernel.py` — reason: 
- `system_v4/probes/sim_gudhi_s2_topology_recovery.py` — reason: 
- `system_v4/probes/sim_holevo_bound_canonical.py` — reason: 
- `system_v4/probes/sim_l6_binding_radius_sweep.py` — reason: 
- `system_v4/probes/sim_layer_stacking_coexistence.py` — reason: 
- `system_v4/probes/sim_layer_stacking_nonprefix.py` — reason: 
- `system_v4/probes/sim_layer_triple_catalog.py` — reason: state construction and ALL entropy computations
- `system_v4/probes/sim_leggett_garg_k3_canonical.py` — reason: placeholder -- filled below
- `system_v4/probes/sim_logarithmic_negativity_werner_canonical.py` — reason: 
- `system_v4/probes/sim_phase7_baseline_validation.py` — reason: 
- `system_v4/probes/sim_pure_lego_berry_curvature_stokes.py` — reason: 
- `system_v4/probes/sim_pure_lego_berry_phase_u1_abelian.py` — reason: 
- `system_v4/probes/sim_pure_lego_cross_shell_coupling_cp1_bures.py` — reason: Complex128 quantum algebra: density matrices, QFI via eigendecomposition, Bures distance, Fubini-Stu
- `system_v4/probes/sim_pure_lego_gauss_bonnet_cp1.py` — reason: Load-bearing: torch.float64 tensors carry the θ and φ quadrature grids; all integrand values K(θ,φ)·
- `system_v4/probes/sim_pure_lego_pairwise_shell_coupling_cp1.py` — reason: Load-bearing: torch.float64 tensors carry all coupling residuals. Jacobi ODE residuals |J''(s)+K·J(s
- `system_v4/probes/sim_pyg_capability.py` — reason: tensor/autograd backend -- overwritten on import
- `system_v4/probes/sim_pyg_dynamic_edge_werner.py` — reason: 
- `system_v4/probes/sim_pytorch_capability.py` — reason: under test
- `system_v4/probes/sim_q3_bipartite_analysis.py` — reason: 
- `system_v4/probes/sim_qfi_squeezed_canonical.py` — reason: placeholder -- filled below
- `system_v4/probes/sim_quantum_discord_canonical.py` — reason: 
- `system_v4/probes/sim_quantum_mutual_info_superadditivity_canonical.py` — reason: 
- `system_v4/probes/sim_relative_entropy_of_entanglement_canonical.py` — reason: 
- `system_v4/probes/sim_substrate_insensitive_analysis.py` — reason: 
- `system_v4/probes/sim_superdense_coding_capacity_canonical.py` — reason: placeholder -- filled below
- `system_v4/probes/sim_tools_load_bearing.py` — reason: torch tensors for density matrices and channel ops
- `system_v4/probes/sim_toponetx_state_class_binding.py` — reason: Werner state density matrices as torch tensors; concurrence via autograd
- `system_v4/probes/sim_torch_amplitude_damping.py` — reason: 
- `system_v4/probes/sim_torch_axis0_3qubit.py` — reason: 
- `system_v4/probes/sim_torch_axis0_gradient.py` — reason: 
- `system_v4/probes/sim_torch_bit_flip.py` — reason: 
- `system_v4/probes/sim_torch_channel_composition.py` — reason: 
- `system_v4/probes/sim_torch_constraint_shells_v2.py` — reason: 
- `system_v4/probes/sim_torch_depolarizing.py` — reason: 
- `system_v4/probes/sim_torch_gnn_axis0_seeded.py` — reason: 
- `system_v4/probes/sim_torch_gnn_directional_gate.py` — reason: 
- `system_v4/probes/sim_torch_gnn_extended_training.py` — reason: 
- `system_v4/probes/sim_torch_gnn_gradient_ref_ablation.py` — reason: 
- `system_v4/probes/sim_torch_gnn_loss_regularized.py` — reason: 
- `system_v4/probes/sim_torch_hopf_connection.py` — reason: 
- `system_v4/probes/sim_torch_ratchet_gnn.py` — reason: 
- `system_v4/probes/sim_torch_ratchet_pipeline_v2.py` — reason: 
- `system_v4/probes/sim_torch_shells_displacement_metric.py` — reason: 
- `system_v4/probes/sim_torch_z_dephasing.py` — reason: 
- `system_v4/probes/sim_w_ghz_analytic_resolution.py` — reason: 
- `system_v4/probes/sim_werner_manifold_scan.py` — reason: 
- `system_v4/probes/sim_werner_qwci_gap.py` — reason: 
- `system_v4/probes/sim_weyl_spinor_hopf.py` — reason: spinor construction, overlap computation, tensor ops
- `system_v4/probes/sim_weyl_two_model_crosscheck.py` — reason: torch tensors for spinor cloud generation and overlap computation
- `system_v4/probes/sim_z3_channel_composition_boundary.py` — reason: load_bearing: numerical gradient of I_c boundary surfaces via autograd

### sympy (36)
- `system_v4/probes/sim_SA12_wilczek_zee_curvature_sympy.py` — reason: Load-bearing: symbolic proof of Tr([A,B])=0 and anti-Hermitian commutator inheritance
- `system_v4/probes/sim_assoc_bundle_associated_bundle_coupling_to_g_tower.py` — reason: 
- `system_v4/probes/sim_assoc_bundle_associated_vector_bundle_construction.py` — reason: 
- `system_v4/probes/sim_assoc_bundle_canonical_connection_from_hopf.py` — reason: 
- `system_v4/probes/sim_axis6_canonical.py` — reason: 
- `system_v4/probes/sim_axis6_entropy_decomposition.py` — reason: 
- `system_v4/probes/sim_axis6_rank_coherence.py` — reason: 
- `system_v4/probes/sim_axis7_12_gs_residual_axes.py` — reason: 
- `system_v4/probes/sim_axis7_12_orthogonal_closure.py` — reason: 
- `system_v4/probes/sim_berry_qfi_entangled_path.py` — reason: 
- `system_v4/probes/sim_berry_qfi_shell_paths.py` — reason: 
- `system_v4/probes/sim_dissipative_kraus_shell_compatibility.py` — reason: 
- `system_v4/probes/sim_foundation_pauli_bloch_backprop.py` — reason: 
- `system_v4/probes/sim_frozen_kernel_classification.py` — reason: 
- `system_v4/probes/sim_gstructure_compatibility_coupling.py` — reason: 
- `system_v4/probes/sim_layer_triple_catalog.py` — reason: closed-form entropy formula derivation for L2 Weyl and L3 phase-damping
- `system_v4/probes/sim_lego_povm_measurement.py` — reason: 
- `system_v4/probes/sim_leviathan_explore_as_category_theoretic_pushout.py` — reason: 
- `system_v4/probes/sim_phase_damping_fixed_point_geometry.py` — reason: 
- `system_v4/probes/sim_pure_lego_clifford_weyl_transport.py` — reason: symbolic proof of transport formula R·e1·~R = cos(θ)e1+sin(θ)e2
- `system_v4/probes/sim_pure_lego_hopf_tori_base.py` — reason: symbolic proof of induced metric g_ij and area=2pi^2*sin(2eta)
- `system_v4/probes/sim_pure_lego_pairwise_shell_coupling_cp1.py` — reason: Load-bearing: sp.simplify(d²J/ds²+4·J) = 0 confirmed for J=sin(2s)/2 (Jacobi ODE residual exactly ze
- `system_v4/probes/sim_pure_lego_qfi_wy_qgt.py` — reason: symbolic spot checks and closed-form simplification for pure-math metric relations
- `system_v4/probes/sim_q3_bipartite_analysis.py` — reason: 
- `system_v4/probes/sim_robertson_uncertainty_canonical.py` — reason: placeholder -- filled below
- `system_v4/probes/sim_stinespring_isometric_equivalence_canonical.py` — reason: placeholder -- filled below
- `system_v4/probes/sim_substrate_insensitive_analysis.py` — reason: 
- `system_v4/probes/sim_toponetx_state_class_binding.py` — reason: symbolic Euler characteristic χ=β0-β1+β2 and verification
- `system_v4/probes/sim_tripartite_mi_bug_fix.py` — reason: 
- `system_v4/probes/sim_werner_entanglement_witness_canonical.py` — reason: placeholder -- filled below
- `system_v4/probes/sim_werner_qwci_gap.py` — reason: 
- `system_v4/probes/sim_weyl_spinor_hopf.py` — reason: chirality operator iγ⁵ eigenvalue equation in Clifford algebra
- `system_v4/probes/sim_weyl_two_model_crosscheck.py` — reason: algebraic P_L·P_R=0 projector identity verified symbolically
- `system_v4/probes/sim_z3_channel_boundary_theorem.py` — reason: load_bearing: analytic boundary derivations and quadratic coefficient checks
- `system_v4/probes/sim_z3_quantum_capacity_bound.py` — reason: load_bearing: derive I_c = 1 - H(lambda) - lambda*log(d-1)/log(d) analytically
- `system_v4/probes/sim_z3_s6_unitary_impossibility.py` — reason: load_bearing: analytic derivation of entropy conservation theorem U†SU = S

### z3 (32)
- `system_v4/probes/sim_3qubit_dag_formal_ordering.py` — reason: 
- `system_v4/probes/sim_3qubit_dag_formal_ordering_v2.py` — reason: 
- `system_v4/probes/sim_axis7_12_orthogonal_closure.py` — reason: 
- `system_v4/probes/sim_berry_qfi_entangled_path.py` — reason: 
- `system_v4/probes/sim_bridge_z3_kernel_ordering.py` — reason: 
- `system_v4/probes/sim_constraint_manifold_L0_L1.py` — reason: SAT/UNSAT admissibility by dimension plus bounded fence-valid assignment counting
- `system_v4/probes/sim_cvc5_shells_crosscheck.py` — reason: primary UNSAT solver; claims sourced from v2
- `system_v4/probes/sim_dissipative_kraus_shell_compatibility.py` — reason: 
- `system_v4/probes/sim_foundation_pauli_bloch_backprop.py` — reason: 
- `system_v4/probes/sim_gstructure_compatibility_coupling.py` — reason: 
- `system_v4/probes/sim_layer_stacking_coexistence.py` — reason: 
- `system_v4/probes/sim_layer_triple_catalog.py` — reason: UNSAT proof that no two layers share (entropy,probe,operator) triple
- `system_v4/probes/sim_lego_choi_state_duality.py` — reason: 
- `system_v4/probes/sim_phase_damping_fixed_point_geometry.py` — reason: 
- `system_v4/probes/sim_pyg_dynamic_edge_werner.py` — reason: 
- `system_v4/probes/sim_toponetx_state_class_binding.py` — reason: UNSAT proof: r<0.17 AND r>0.17 is unsatisfiable (disjoint regimes)
- `system_v4/probes/sim_torch_amplitude_damping.py` — reason: 
- `system_v4/probes/sim_torch_bit_flip.py` — reason: 
- `system_v4/probes/sim_torch_constraint_shells_v2.py` — reason: 
- `system_v4/probes/sim_torch_depolarizing.py` — reason: 
- `system_v4/probes/sim_torch_graph_integrated_pipeline.py` — reason: 
- `system_v4/probes/sim_torch_phase_damping.py` — reason: 
- `system_v4/probes/sim_torch_ratchet_pipeline_v2.py` — reason: 
- `system_v4/probes/sim_torch_z_dephasing.py` — reason: 
- `system_v4/probes/sim_tripartite_mi_bug_fix.py` — reason: 
- `system_v4/probes/sim_werner_manifold_scan.py` — reason: 
- `system_v4/probes/sim_werner_qwci_gap.py` — reason: 
- `system_v4/probes/sim_weyl_spinor_hopf.py` — reason: UNSAT proof: same-sheet collision is contradictory
- `system_v4/probes/sim_weyl_two_model_crosscheck.py` — reason: UNSAT proof that both models cannot share combined β0
- `system_v4/probes/sim_z3_dephasing_symmetry_guard.py` — reason: load_bearing: SMT UNSAT for dephasing symmetry, negativity boundary, and relay disconnection
- `system_v4/probes/sim_z3_fence_exhaustive_negatives.py` — reason: load_bearing: SAT/UNSAT verdicts for every fence-removal and pairwise-removal test in the exhaustive
- `system_v4/probes/sim_z3_s6_unitary_impossibility.py` — reason: load_bearing: four SAT/UNSAT proofs that S6 entropy increase is impossible under unitary evolution

### rustworkx (16)
- `system_v4/probes/sim_3qubit_dag_formal_ordering.py` — reason: 
- `system_v4/probes/sim_3qubit_dag_formal_ordering_v2.py` — reason: 
- `system_v4/probes/sim_axis6_rank_coherence.py` — reason: 
- `system_v4/probes/sim_bridge_phi0_proof_integration.py` — reason: 
- `system_v4/probes/sim_bridge_z3_kernel_ordering.py` — reason: 
- `system_v4/probes/sim_c2_topology_expansion.py` — reason: 
- `system_v4/probes/sim_foundation_shell_graph_topology.py` — reason: 
- `system_v4/probes/sim_layer_triple_catalog.py` — reason: DAG of layer coupling: edges where native operator preserves target entropy
- `system_v4/probes/sim_lego_weyl_hypergraph_local.py` — reason: load-bearing DAG schedule for local carrier assembly order
- `system_v4/probes/sim_pyg_dynamic_edge_werner.py` — reason: 
- `system_v4/probes/sim_rustworkx_deep_cayley_s4_admissibility.py` — reason: LOAD-BEARING: cycle_basis, is_isomorphic, is_connected, max_flow, edge_connectivity decide the struc
- `system_v4/probes/sim_tools_load_bearing.py` — reason: DAG topological sort determines channel order -- test 1
- `system_v4/probes/sim_torch_constraint_shells_v2.py` — reason: 
- `system_v4/probes/sim_torch_shells_displacement_metric.py` — reason: 
- `system_v4/probes/sim_torch_shells_gradient_flow.py` — reason: 
- `system_v4/probes/sim_weyl_two_model_crosscheck.py` — reason: DAG encoding Model A / Model B as parallel branches preceding Weyl_shell

### clifford (15)
- `system_v4/probes/sim_assoc_bundle_weyl_spinor_as_section.py` — reason: 
- `system_v4/probes/sim_axis6_entropy_decomposition.py` — reason: 
- `system_v4/probes/sim_axis6_rank_coherence.py` — reason: 
- `system_v4/probes/sim_clifford_capability.py` — reason: under test
- `system_v4/probes/sim_compound_operator_geometry.py` — reason: Cl(3) rotor/dephasing cross-check is part of the core comparison
- `system_v4/probes/sim_constraint_manifold_L2_L3.py` — reason: Cl(p) hierarchy establishes the minimum carrier algebra needed for SU(2)-grade rotor structure
- `system_v4/probes/sim_layer_triple_catalog.py` — reason: Cl(3) rotor for SU(2) Hopf rotation (L1 native operator)
- `system_v4/probes/sim_leggett_garg_k3_clifford_canonical.py` — reason: placeholder -- filled below
- `system_v4/probes/sim_operator_geometry_compatibility.py` — reason: load-bearing for native Cl(3) rotor action
- `system_v4/probes/sim_phase_damping_fixed_point_geometry.py` — reason: 
- `system_v4/probes/sim_pure_lego_clifford_weyl_transport.py` — reason: PRIMARY: Cl(3) rotors, sandwich product, double-cover, non-commutativity
- `system_v4/probes/sim_q2_clifford_structure.py` — reason: 
- `system_v4/probes/sim_weyl_geometry_ladder_audit.py` — reason: load_bearing: TORUS_CLIFFORD manifold case provides the neutral-witness discriminator separating amb
- `system_v4/probes/sim_weyl_spinor_hopf.py` — reason: Cl(3) bivector e12/e21 chirality algebra
- `system_v4/probes/sim_weyl_two_model_crosscheck.py` — reason: Cl(3) spinor exponential map for Model A L/R fiber generation

### pyg (11)
- `system_v4/probes/sim_axis0_pyg_proxy.py` — reason: 
- `system_v4/probes/sim_geometric_constraint_manifold_pyg.py` — reason: 
- `system_v4/probes/sim_pyg_capability.py` — reason: tool under capability test -- overwritten on import
- `system_v4/probes/sim_torch_gnn_axis0_seeded.py` — reason: 
- `system_v4/probes/sim_torch_gnn_directional_gate.py` — reason: 
- `system_v4/probes/sim_torch_gnn_extended_training.py` — reason: 
- `system_v4/probes/sim_torch_gnn_gradient_ref_ablation.py` — reason: 
- `system_v4/probes/sim_torch_gnn_loss_regularized.py` — reason: 
- `system_v4/probes/sim_torch_graph_integrated_pipeline.py` — reason: 
- `system_v4/probes/sim_torch_ratchet_gnn.py` — reason: 
- `system_v4/probes/sim_torch_ratchet_pipeline_v2.py` — reason: 

### toponetx (8)
- `system_v4/probes/sim_constraint_manifold_L2_L3.py` — reason: cell-complex discretization and shell structure checks for torus carrier realizations
- `system_v4/probes/sim_gerbe_coupling_nested_hopf.py` — reason: 
- `system_v4/probes/sim_gerbe_reduction_coboundary.py` — reason: 
- `system_v4/probes/sim_gerbe_structure_b_field_cochain.py` — reason: 
- `system_v4/probes/sim_lego_weyl_hypergraph_local.py` — reason: load-bearing cell-complex lift and boundary composition check
- `system_v4/probes/sim_toponetx_capability.py` — reason: 
- `system_v4/probes/sim_toponetx_state_class_binding.py` — reason: CellComplex construction and Betti number computation
- `system_v4/probes/sim_torch_graph_integrated_pipeline.py` — reason: 

### cvc5 (6)
- `system_v4/probes/sim_axis6_canonical.py` — reason: 
- `system_v4/probes/sim_bridge_cvc5_crosscheck.py` — reason: 
- `system_v4/probes/sim_bridge_extended_proofs.py` — reason: 
- `system_v4/probes/sim_bridge_phi0_proof_integration.py` — reason: 
- `system_v4/probes/sim_cvc5_amplitude_damping_boundary.py` — reason: 
- `system_v4/probes/sim_z3_channel_composition_boundary.py` — reason: load_bearing: SyGuS minimal generator synthesis for each boundary polynomial

### e3nn (6)
- `system_v4/probes/sim_e3nn_capability.py` — reason: under test
- `system_v4/probes/sim_e3nn_hopf_spinor_equivariance.py` — reason: PRIMARY: irreps, Linear, wigner_D, rand_angles, chirality via parity
- `system_v4/probes/sim_e3nn_ic_invariance.py` — reason: PRIMARY: generate SU(2) rotations via wigner_D; FCTP equivariance pipeline
- `system_v4/probes/sim_e3nn_relay_equivariance.py` — reason: PRIMARY: FullyConnectedTensorProduct, Irreps, wigner_D for equivariance test
- `system_v4/probes/sim_e3nn_tensor_product.py` — reason: PRIMARY: FullyConnectedTensorProduct, Irreps, wigner_D, rand_angles
- `system_v4/probes/sim_tools_load_bearing.py` — reason: equivariant channel selector via Wigner-D -- test 5

### geomstats (4)
- `system_v4/probes/sim_assoc_bundle_parallel_transport_admissibility.py` — reason: 
- `system_v4/probes/sim_axis6_canonical.py` — reason: 
- `system_v4/probes/sim_bridge_phi0_proof_integration.py` — reason: 
- `system_v4/probes/sim_weyl_two_model_crosscheck.py` — reason: geodesic distance L↔R on S³ for Model B vs Model A comparison

### gudhi (4)
- `system_v4/probes/sim_gudhi_bipartite_entangled.py` — reason: 
- `system_v4/probes/sim_gudhi_phase_sensitive_kernel.py` — reason: 
- `system_v4/probes/sim_weyl_spinor_hopf.py` — reason: persistent homology of combined L+R Weyl fiber bundle
- `system_v4/probes/sim_weyl_two_model_crosscheck.py` — reason: persistent homology β0/β1 on L+R combined point clouds for both models

### xgi (2)
- `system_v4/probes/sim_pyg_dynamic_edge_werner.py` — reason: 
- `system_v4/probes/sim_toponetx_state_class_binding.py` — reason: hyperedge model: L4/L6 regimes + QWCI gap as three hyperedges

## Non-canonical HIGH

### pyg (2)
- `system_v4/probes/sim_compound_z3_clifford_pyg_so3_admissibility.py` [cls=None]
- `system_v4/probes/sim_pyg_deep_oversmoothing_bound.py` [cls=None]

### z3 (1)
- `system_v4/probes/sim_compound_z3_clifford_pyg_so3_admissibility.py` [cls=None]

### clifford (1)
- `system_v4/probes/sim_compound_z3_clifford_pyg_so3_admissibility.py` [cls=None]
