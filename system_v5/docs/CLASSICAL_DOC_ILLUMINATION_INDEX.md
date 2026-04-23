# CLASSICAL_DOC_ILLUMINATION_INDEX

Generated 2026-04-14. Scans `system_v4/probes/classical_baseline_*.py` and `sim_*_baseline_*.py` for scope_note / docstring content, doc citations, and substring-matched nonclassical pairs.

Totals: 101 classical sims; 1 cite a doc; 60 have a paired nonclassical candidate.

## Illumination Table

| sim_path | topic | doc_illuminated | paired_nonclassical |
|---|---|---|---|
| system_v4/probes/classical_baseline_aes_sbox_verify.py | aes_sbox_verify — classical_baseline: AES S-box bijection subset |  |  |
| system_v4/probes/classical_baseline_barabasi_albert.py | barabasi_albert — classical_baseline: Barabasi-Albert preferential attachment |  |  |
| system_v4/probes/classical_baseline_belousov_zhabotinsky.py | belousov_zhabotinsky — classical_baseline: Oregonator BZ toy |  |  |
| system_v4/probes/classical_baseline_benjamin_feir.py | benjamin_feir — classical_baseline: Benjamin-Feir NLS check |  |  |
| system_v4/probes/classical_baseline_bisection.py | bisection — classical_baseline_bisection.py -- non-canon, lane_B-eligible |  |  |
| system_v4/probes/classical_baseline_bloom_filter.py | bloom_filter — classical_baseline: Bloom filter FP rate |  |  |
| system_v4/probes/classical_baseline_boids.py | boids — classical_baseline: Boids flocking |  |  |
| system_v4/probes/classical_baseline_carnot_efficiency.py | carnot_efficiency — classical baseline carnot efficiency |  | sim_classical_carnot_efficiency_vs_reservoir.py |
| system_v4/probes/classical_baseline_cellular_automaton.py | cellular_automaton — classical_baseline_cellular_automaton.py -- non-canon, lane_B-eligible |  | sim_leviathan_explore_as_cellular_automaton.py |
| system_v4/probes/classical_baseline_cholesky_spd.py | cholesky_spd — classical_baseline_cholesky_spd.py -- non-canon, lane_B-eligible |  |  |
| system_v4/probes/classical_baseline_cl3_rotor_pauli_rep.py | cl3_rotor_pauli_rep — classical baseline cl3 rotor pauli rep |  | sim_pauli_algebra_relations.py |
| system_v4/probes/classical_baseline_cl6_kron_pauli_rep.py | cl6_kron_pauli_rep — classical baseline cl6 kron pauli rep |  | sim_pauli_algebra_relations.py |
| system_v4/probes/classical_baseline_collatz_trajectory.py | collatz_trajectory — classical_baseline: Collatz trajectory |  | sim_geomstats_ratchet_trajectory.py |
| system_v4/probes/classical_baseline_dla_aggregation.py | dla_aggregation — classical_baseline_dla_aggregation.py -- non-canon, lane_B-eligible |  |  |
| system_v4/probes/classical_baseline_em_gmm.py | em_gmm — classical_baseline: EM for 1D GMM (2 components) |  |  |
| system_v4/probes/classical_baseline_erdos_renyi.py | erdos_renyi — classical_baseline: Erdos-Renyi random graph |  | sim_renyi_entropy_classical.py |
| system_v4/probes/classical_baseline_eulerian_path.py | eulerian_path — classical_baseline_eulerian_path.py -- non-canon, lane_B-eligible |  | sim_berry_qfi_shell_paths.py |
| system_v4/probes/classical_baseline_fep_gaussian_vfe.py | fep_gaussian_vfe — classical baseline fep gaussian vfe |  | sim_sympy_gaussian_integral.py |
| system_v4/probes/classical_baseline_fep_predictive_coding.py | fep_predictive_coding — classical baseline fep predictive coding |  | sim_superdense_coding_capacity_canonical.py |
| system_v4/probes/classical_baseline_fft_reconstruction.py | fft_reconstruction — classical_baseline_fft_reconstruction.py -- non-canon, lane_B-eligible |  | sim_holodeck_reality_reconstruction_probe.py |
| system_v4/probes/classical_baseline_fibonacci_spiral.py | fibonacci_spiral — classical_baseline: Fibonacci spiral |  |  |
| system_v4/probes/classical_baseline_game_of_life.py | game_of_life — classical_baseline: Conway Game of Life |  | sim_pure_lego_games_bayesian_largedev.py |
| system_v4/probes/classical_baseline_gillespie_ssa.py | gillespie_ssa — classical_baseline: Gillespie SSA (A->B) |  |  |
| system_v4/probes/classical_baseline_goldbach_check.py | goldbach_check — classical_baseline: Goldbach check up to N |  | sim_cvc5_shells_crosscheck.py |
| system_v4/probes/classical_baseline_golden_ratio_convergence.py | golden_ratio_convergence — classical_baseline: Fibonacci ratio -> phi |  | sim_monotone_filtration_convergence_classical.py |
| system_v4/probes/classical_baseline_gradient_descent_convex.py | gradient_descent_convex — classical_baseline_gradient_descent_convex.py -- non-canon, lane_B-eligible |  | sim_autograd_vfe_descent.py |
| system_v4/probes/classical_baseline_gram_schmidt.py | gram_schmidt — classical_baseline_gram_schmidt.py -- non-canon, lane_B-eligible |  | sim_schmidt_mode_truncation.py |
| system_v4/probes/classical_baseline_graph_laplacian_spectrum.py | graph_laplacian_spectrum — classical_baseline: Graph Laplacian spectrum |  | sim_hypergraph_laplacian_spectrum_classical.py |
| system_v4/probes/classical_baseline_group_reps_s3_d4.py | group_reps_s3_d4 — classical_baseline_group_reps_s3_d4.py -- non-canon, lane_B-eligible |  | sim_gauge_group_correspondence.py |
| system_v4/probes/classical_baseline_hamming_code.py | hamming_code — classical_baseline: Hamming(7,4) correction |  | sim_lego_toric_code.py |
| system_v4/probes/classical_baseline_heat_equation_fd.py | heat_equation_fd — classical_baseline_heat_equation_fd.py -- non-canon, lane_B-eligible |  | sim_classical_master_equation_classical.py |
| system_v4/probes/classical_baseline_henon_map.py | henon_map — classical_baseline: Henon map |  |  |
| system_v4/probes/classical_baseline_hermitian_spectral.py | hermitian_spectral — classical baseline hermitian spectral |  | sim_qpca_spectral_extraction_classical.py |
| system_v4/probes/classical_baseline_hmm_viterbi.py | hmm_viterbi — classical_baseline: HMM Viterbi decoding |  |  |
| system_v4/probes/classical_baseline_hofstadter_butterfly.py | hofstadter_butterfly — classical_baseline: Hofstadter butterfly (one phi) |  |  |
| system_v4/probes/classical_baseline_holodeck_carrier_equality.py | holodeck_carrier_equality — classical baseline holodeck carrier equality |  | sim_holodeck_atom_1_carrier.py |
| system_v4/probes/classical_baseline_holodeck_reduction_quotient.py | holodeck_reduction_quotient — classical baseline holodeck reduction quotient |  | sim_holodeck_atom_3_reduction.py |
| system_v4/probes/classical_baseline_holodeck_structure_composition.py | holodeck_structure_composition — classical baseline holodeck structure composition |  | sim_holodeck_atom_2_structure.py |
| system_v4/probes/classical_baseline_hopf_fibration.py | hopf_fibration — classical baseline hopf fibration |  | sim_hopf_fibration_embedding_classical.py |
| system_v4/probes/classical_baseline_huffman_coding.py | huffman_coding — classical_baseline: Huffman prefix-free |  | sim_superdense_coding_capacity_canonical.py |
| system_v4/probes/classical_baseline_hyperloglog_cardinality.py | hyperloglog_cardinality — classical_baseline: HyperLogLog estimate |  | sim_f01n01_lego_08_equiv_class_cardinality_2q.py |
| system_v4/probes/classical_baseline_igt_admissibility_dominance.py | igt_admissibility_dominance — classical baseline igt admissibility dominance |  | sim_mirror_4_admissibility.py |
| system_v4/probes/classical_baseline_igt_nash_2x2.py | igt_nash_2x2 — classical baseline igt nash 2x2 |  |  |
| system_v4/probes/classical_baseline_ising2d_metropolis.py | ising2d_metropolis — classical_baseline_ising2d_metropolis.py -- non-canon, lane_B-eligible |  |  |
| system_v4/probes/classical_baseline_ising_3d.py | ising_3d — classical_baseline: Ising 3D Metropolis |  | sim_axis0_coarising_stress_test.py |
| system_v4/probes/classical_baseline_jacobi_eigen.py | jacobi_eigen — classical_baseline_jacobi_eigen.py -- non-canon, lane_B-eligible |  | sim_eigenvalue_spectrum_view_classical.py |
| system_v4/probes/classical_baseline_julia_set.py | julia_set — classical_baseline: Julia set for c=-0.8+0.156j |  |  |
| system_v4/probes/classical_baseline_kmeans_clustering.py | kmeans_clustering — classical_baseline: k-means clustering |  | sim_xgi_deep_hypergraph_clustering.py |
| system_v4/probes/classical_baseline_koch_snowflake.py | koch_snowflake — classical_baseline: Koch snowflake perimeter |  | sim_kochen_specker_18ray_canonical.py |
| system_v4/probes/classical_baseline_kuramoto_sync.py | kuramoto_sync — classical_baseline_kuramoto_sync.py -- non-canon, lane_B-eligible |  |  |
| system_v4/probes/classical_baseline_l_systems_plant.py | l_systems_plant — classical_baseline: L-system plant string |  |  |
| system_v4/probes/classical_baseline_lanczos_tridiag.py | lanczos_tridiag — classical_baseline_lanczos_tridiag.py -- non-canon, lane_B-eligible |  |  |
| system_v4/probes/classical_baseline_leviathan_coalition_stability.py | leviathan_coalition_stability — classical baseline leviathan coalition stability |  | sim_leviathan_explore_as_category_theoretic_pushout.py |
| system_v4/probes/classical_baseline_leviathan_monotone_aggregation.py | leviathan_monotone_aggregation — classical baseline leviathan monotone aggregation |  | sim_leviathan_explore_as_category_theoretic_pushout.py |
| system_v4/probes/classical_baseline_logistic_bifurcation.py | logistic_bifurcation — classical_baseline_logistic_bifurcation.py -- non-canon, lane_B-eligible |  |  |
| system_v4/probes/classical_baseline_lorenz_attractor.py | lorenz_attractor — classical_baseline_lorenz_attractor.py -- non-canon, lane_B-eligible |  | sim_axis0_attractor_basin_boundary.py |
| system_v4/probes/classical_baseline_lotka_volterra.py | lotka_volterra — classical_baseline: Lotka-Volterra |  |  |
| system_v4/probes/classical_baseline_lu_decomposition.py | lu_decomposition — classical_baseline_lu_decomposition.py -- non-canon, lane_B-eligible |  | sim_pure_lego_gates_decompositions.py |
| system_v4/probes/classical_baseline_lz77_compression.py | lz77_compression — classical_baseline: LZ77 roundtrip |  | sim_axis0_fep_compression_framing.py |
| system_v4/probes/classical_baseline_mandelbrot_bifurcation.py | mandelbrot_bifurcation — classical_baseline: Logistic bifurcation (real axis) |  |  |
| system_v4/probes/classical_baseline_mandelbrot_set.py | mandelbrot_set — classical_baseline: Mandelbrot set membership |  |  |
| system_v4/probes/classical_baseline_matrix_exp_pade.py | matrix_exp_pade — classical_baseline_matrix_exp_pade.py -- non-canon, lane_B-eligible |  | sim_pure_lego_ml_density_matrix.py |
| system_v4/probes/classical_baseline_miller_rabin.py | miller_rabin — classical_baseline: Miller-Rabin |  |  |
| system_v4/probes/classical_baseline_monte_carlo_pi.py | monte_carlo_pi — classical_baseline_monte_carlo_pi.py -- non-canon, lane_B-eligible |  |  |
| system_v4/probes/classical_baseline_moran_model.py | moran_model — classical_baseline: Moran model absorption |  | sim_fep_generative_model_as_shell.py |
| system_v4/probes/classical_baseline_navier_stokes_2d_simplified.py | navier_stokes_2d_simplified — classical_baseline: Navier-Stokes 2D (viscous vorticity diffusion) |  | sim_pure_lego_stokes_mueller.py |
| system_v4/probes/classical_baseline_newton_root.py | newton_root — classical_baseline_newton_root.py -- non-canon, lane_B-eligible |  | sim_cvc5_deep_nra_primitive_root_unity.py |
| system_v4/probes/classical_baseline_pagerank_iter.py | pagerank_iter — classical_baseline_pagerank_iter.py -- non-canon, lane_B-eligible |  | sim_pagerank_classical.py |
| system_v4/probes/classical_baseline_penrose_tiling.py | penrose_tiling — classical_baseline: Penrose substitution golden ratio |  |  |
| system_v4/probes/classical_baseline_percolation_2d.py | percolation_2d — classical_baseline_percolation_2d.py -- non-canon, lane_B-eligible |  | sim_leviathan_explore_as_percolation_network.py |
| system_v4/probes/classical_baseline_poisson_solver_jacobi.py | poisson_solver_jacobi — classical_baseline: Poisson solver (Jacobi) |  | sim_sympy_jacobi_su2.py |
| system_v4/probes/classical_baseline_potts_model.py | potts_model — classical_baseline: q-state Potts |  | sim_fep_generative_model_as_shell.py |
| system_v4/probes/classical_baseline_power_iteration.py | power_iteration — classical_baseline_power_iteration.py -- non-canon, lane_B-eligible |  |  |
| system_v4/probes/classical_baseline_predator_prey_rosenzweig.py | predator_prey_rosenzweig — classical_baseline: Rosenzweig-MacArthur |  |  |
| system_v4/probes/classical_baseline_prime_sieve.py | prime_sieve — classical_baseline: Sieve of Eratosthenes |  |  |
| system_v4/probes/classical_baseline_qr_decomposition.py | qr_decomposition — classical_baseline_qr_decomposition.py -- non-canon, lane_B-eligible |  | sim_pure_lego_gates_decompositions.py |
| system_v4/probes/classical_baseline_ramanujan_nagell.py | ramanujan_nagell — classical_baseline: Ramanujan-Nagell solutions |  |  |
| system_v4/probes/classical_baseline_random_walk_mixing.py | random_walk_mixing — classical baseline random walk mixing |  | sim_pure_lego_random_circuits_typicality.py |
| system_v4/probes/classical_baseline_reaction_diffusion_turing.py | reaction_diffusion_turing — classical_baseline: Gray-Scott Turing |  |  |
| system_v4/probes/classical_baseline_reed_solomon_toy.py | reed_solomon_toy — classical_baseline: Reed-Solomon toy (poly interp) |  |  |
| system_v4/probes/classical_baseline_rk4_ode.py | rk4_ode — classical_baseline_rk4_ode.py -- non-canon, lane_B-eligible |  |  |
| system_v4/probes/classical_baseline_robinson_tiles.py | robinson_tiles — classical_baseline: Robinson tile matching toy |  | sim_pure_lego_qca_lieb_robinson.py |
| system_v4/probes/classical_baseline_rsa_toy_keygen.py | rsa_toy_keygen — classical_baseline: RSA toy |  |  |
| system_v4/probes/classical_baseline_sci_method_bayes_update.py | sci_method_bayes_update — classical baseline sci method bayes update |  | sim_sci_method_atom_3_reduction.py |
| system_v4/probes/classical_baseline_sci_method_modus_tollens.py | sci_method_modus_tollens — classical baseline sci method modus tollens |  | sim_sci_method_atom_3_reduction.py |
| system_v4/probes/classical_baseline_shannon_entropy_source.py | shannon_entropy_source — classical_baseline: Shannon entropy |  | sim_shannon_entropy.py |
| system_v4/probes/classical_baseline_sierpinski_ifs.py | sierpinski_ifs — classical_baseline: Sierpinski IFS chaos game |  |  |
| system_v4/probes/classical_baseline_simplex_euler_char.py | simplex_euler_char — classical_baseline_simplex_euler_char.py -- non-canon, lane_B-eligible |  | sim_euler_characteristic_classical.py |
| system_v4/probes/classical_baseline_simpson_integration.py | simpson_integration — classical_baseline_simpson_integration.py -- non-canon, lane_B-eligible |  | sim_bridge_chain_integration.py |
| system_v4/probes/classical_baseline_simulated_annealing_tsp.py | simulated_annealing_tsp — classical_baseline_simulated_annealing_tsp.py -- non-canon, lane_B-eligible |  |  |
| system_v4/probes/classical_baseline_sir_epidemic.py | sir_epidemic — classical_baseline: SIR epidemic ODE |  |  |
| system_v4/probes/classical_baseline_svd_reconstruction.py | svd_reconstruction — classical baseline svd reconstruction |  | sim_holodeck_reality_reconstruction_probe.py |
| system_v4/probes/classical_baseline_szilard_onebit.py | szilard_onebit — classical baseline szilard onebit |  | sim_qit_szilard_record_ordering_refinement_translation_lane.py |
| system_v4/probes/classical_baseline_u1_phase_loop.py | u1_phase_loop — classical baseline u1 phase loop |  | sim_neg_loop_law_swap.py |
| system_v4/probes/classical_baseline_vicsek_flocking.py | vicsek_flocking — classical_baseline: Vicsek flocking |  |  |
| system_v4/probes/classical_baseline_watts_strogatz.py | watts_strogatz — classical_baseline: Watts-Strogatz small-world |  |  |
| system_v4/probes/classical_baseline_wave_equation_1d.py | wave_equation_1d — classical_baseline_wave_equation_1d.py -- non-canon, lane_B-eligible |  | sim_classical_master_equation_classical.py |
| system_v4/probes/classical_baseline_wigner_semicircle.py | wigner_semicircle — classical_baseline_wigner_semicircle.py -- non-canon, lane_B-eligible |  | sim_pure_lego_wigner_quasiprobability.py |
| system_v4/probes/classical_baseline_wright_fisher.py | wright_fisher — classical_baseline: Wright-Fisher drift |  | sim_fisher_dpi_coupling_classical.py |
| system_v4/probes/classical_baseline_xy_model.py | xy_model — classical_baseline: XY Monte Carlo |  | sim_fep_generative_model_as_shell.py |
| system_v4/probes/sim_phase7_baseline_validation.py | phase7 — Phase 7 Baseline Validation -- Falsification Protocol | PYTORCH_RATCHET_BUILD_PLAN.md | sim_phase7_divergence_analysis.py |

## Doc coverage

Docs with >=1 classical illuminator (1):

- PYTORCH_RATCHET_BUILD_PLAN.md (1)

Docs with 0 classical illuminators (54):

- 00_manifest.md
- 01_pca_qpca_alignment.md
- 02_compression_to_density_matrix_map.md
- 03_source_notes.md
- 04_system_math_alignment.md
- 05_research_index.md
- 06_entropy_sweep_protocol.md
- 07_model_math_geometry_sim_plan.md
- 08_aligned_sim_backlog_and_build_order.md
- 09_research_inventory_and_foundations.md
- 10_cross_domain_equivalence_map.md
- 11_mass_equivalence_engine.md
- 12_mimetic_meme_manifold_harness.md
- 13_mimetic_meme_manifold_source_map.md
- 14_mimetic_meme_manifold_canonical_synthesis.md
- 15_stack_authority_and_capability_index.md
- 16_lego_build_catalog.md
- 17_actual_lego_registry.md
- AGENT_WORKFLOW_AND_BOOT_ARCHITECTURE.md
- ANOMALOUS_COMPUTER_SCIENCE_TRANSLATION.md
- AUDIT_PLATONIC_RESIDUE_AND_GAPS.md
- AXIS_AND_ENTROPY_REFERENCE.md
- BATTERY_INDEX.md
- BOOT_PROMPT_TEMPLATES.md
- CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md
- CONSTRAINT_SURFACE_AND_PROCESS.md
- CURRENT_DOCS_MAP.md
- ENFORCEMENT_AND_PROCESS_RULES.md
- ENGINE_MATH_REFERENCE.md
- EXPLICIT_CONTROLLER_MODEL.md
- EXTERNAL_MATH_EML_OPERATOR.md
- FALSIFICATION_SIM_DESIGNS.md
- LADDERS_FENCES_ADMISSION_REFERENCE.md
- LEGACY_CONTEXT_AND_GENEALOGY.md
- LEGO_SIM_CONTRACT.md
- LLM_CONTROLLER_CONTRACT.md
- MIGRATION_REGISTRY.md
- NOMINALISM_IN_THIS_SYSTEM.md
- NOMINALIST_CS_AND_JP_SYSTEMS_TERMS.md
- OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md
- OWNER_THESIS_AND_COSMOLOGY.md
- SESSION_DEEP_CORRECTIONS_2026_04_05.md
- SESSION_HANDOFF_2026_04_07.md
- SIM_CORRECTIONS_AND_CLASSIFICATIONS.md
- SIM_SESSION_INDEX.md
- SYSTEM_ARCHITECTURE_REFERENCE.md
- TIER_STATUS.md
- TODO.md
- TOOLING_STATUS.md
- TOOL_LEGO_INTEGRATION_MATRIX.md
- TOOL_MANIFEST_AUDIT.md
- TRADITION_SYSTEM_MAPPING_DETAILED.md
- V5_CONTENT_GAP_ANALYSIS.md
- VENV_MIGRATION_STATUS.md
