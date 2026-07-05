# Assembly Inventory 2026-07-04

Owner direction: "most of the work has been done, it just needs to be put together right, and fully run with the 3 sim engines."

Scope searched: direct filesystem reads only, no MCP. I searched `system_v5/`, `system_v6/`, and `system_v7/`, with emphasis on `system_v7/sims/`, `system_v5/julia_carrier/`, `system_v5/ops/formal_scouts/`, `system_v5/legos/`, and result JSON under those trees. I checked result files for actual engine legs instead of trusting names. I did not freshly rerun sims in this inventory.

Status vocabulary:

- `READY`: existing result files show the rung has a 3-engine or declared all-three implementation with local pass/agreement evidence. This still needs a fresh owner-requested full rerun before promotion.
- `RERUN`: implementation exists, but result evidence is stale, partial, missing one or more legs, or not packaged as a clean 3-engine tower rung.
- `GAP`: no found implementation directly instantiates the rung.
- `OPEN`: intentionally not closed by current repo evidence.

## Rung Map

| Rung | Tower object | Best existing sim/result paths | Result JSON present? | Engine legs genuinely observed | Honest status | Verdict |
|---|---|---|---:|---|---|---|
| G0 | finite support | `system_v7/sims/finite_ring_checkerboard_support_three_presentation_consistency_v0/`; `results/*exact_results.json`, `*jax_results.json`, `*agreement_results.json`; support legos in `system_v5/legos/finite_support_topology_entropy_witness_pyg_gudhi_xgi_z3.py` | yes | exact/numpy-style Python + jax; no Julia/PyTorch leg found for the v7 support sim | exists/runs as finite support/chart consistency; not full three-engine | RERUN |
| G1 | `~_P` indistinguishability | `system_v7/sims/distinguishability_quotient_floor_v0/`; `system_v7/sims/finite_distinguishability_quotient_forced_or_installed_carrier_v0/`; `system_v5/julia_carrier/results/foundation_r0_distinguishability_julia_results.json` plus JAX/PyTorch scout legs in `system_v5/ops/formal_scouts/foundation_r0_distinguishability_*` | yes | julia, jax, pytorch in v7 quotient-floor/forced-installed result sets | exists/runs with 3 legs, scratch ceiling | READY |
| G2 | probe quotient | `system_v7/sims/finite_probe_quotient_inverse_limit_tower_1q_through_4q/`; `system_v5/julia_carrier/r0_r1_r2_probe_quotient_micro_packet_julia_results.json`; `system_v5/julia_carrier/results/foundation_r2_quotient_stability_julia_results.json` plus JAX/PyTorch formal-scout legs | yes | julia, jax, pytorch in v7 inverse-limit quotient sim; Julia-only older micro packet | exists/runs with 3 legs, scratch ceiling | READY |
| G3 | survivor tower/carves | `system_v7/sims/independent_survivor_restriction_noncommutation_verify_v0/`; `system_v7/sims/survivor_set_running_mean_threshold_noncommutation_v0/`; `system_v7/sims/induced_geometry_on_survivors_v0/`; `system_v5/ops/formal_scouts/sim_gamma5_offdiagonal_coherence_trace_orbit_survivor_quotient_probe.py` | yes | julia, jax, pytorch observed in `independent_survivor_restriction_noncommutation_verify_v0_agreement_results.json`; some survivor/geometry variants are exact+jax only | exists/runs; best 3-leg survivor restriction is ready, later carve variants need rerun | READY |
| G4 | history/updates (N01) | `system_v7/sims/ordered_channel_maps_noncommutation_matrix_v0/`; `system_v7/sims/order_sensitivity_noncommutation_floor_v0/`; `system_v7/sims/online_regime_shift_detector_v0/`; `system_v7/sims/update_monoid_aperiodicity_control_v0/`; `system_v5/julia_carrier/n01_ordering_forced_carrier_results.json`; `system_v5/julia_carrier/results/foundation_foundation_r1_n01_noncommutation_julia_result.json` plus JAX/PyTorch formal-scout legs | yes | numpy, jax, pytorch, julia in ordered-channel agreement; Julia-only older N01 receipts also present | exists/runs with 3 legs for ordered update/noncommutation matrix | READY |
| G5 | density matrices `D(H)` early carrier; downstream runs on `rho` | `system_v7/sims/carrier_type_admissibility_matrix_v0/`; `system_v5/julia_carrier/density_matrix_spinor_lift_julia_results.json`; `system_v5/julia_carrier/density_matrix_spinor_lift_jax_results.json`; `system_v5/legos/finite_density_matrix_carrier_trace_psd_pytorch_sympy_z3.py`; `system_v5/legos/density_operator_cptp_amplitude_damping_trace_psd_pytorch_sympy_z3.py` | yes | Julia and JAX for density-spinor lift; PyTorch density legos exist; `carrier_type_admissibility_matrix_v0_three_engine_results.json` explicitly scopes Julia+JAX and says PyTorch not scoped | exists but not assembled as one 3-engine rho-first rung | RERUN |
| G6 | spinor sphere `S3` | `system_v5/julia_carrier/clifford_spinor_carrier_rung_julia_results.json`; `system_v5/julia_carrier/jax_clifford_spinor_carrier_smt_results.json`; `system_v5/legos/unit_spinor_hopf_projection_phase_invariance_geomstats_pytorch_sympy.py`; `system_v5/legos/weyl_spinor_chirality_hamiltonian_sign_expectation_clifford_pytorch_z3.py` | yes | Julia, JAX, PyTorch evidence exists across separate files, not one clean rung envelope | exists but scattered | RERUN |
| G7 | Hopf `S3 -> S2`, tori, connection | `system_v5/julia_carrier/hopf_three_ways_julia_results.json`; `system_v5/julia_carrier/hopf_three_ways_jax_results.json`; `system_v5/julia_carrier/hopf_linking_itensors_clifford_result.json`; `system_v5/julia_carrier/jax_clifford_torus_nested_hopf_foliation.py`; `system_v5/julia_carrier/npc_connection_geometry_julia_results.json`; `system_v5/legos/unit_spinor_hopf_projection_phase_invariance_geomstats_pytorch_sympy_results.json` | yes | Julia and JAX Hopf receipts; PyTorch/geomstats Hopf lego; not one all-three Hopf envelope | exists but scattered | RERUN |
| G8 | two sheets `+/- H0` | `system_v5/julia_carrier/weyl_sheet_pair_probe_jax_results.json`; `system_v5/julia_carrier/results/foundation_foundation_r5_weyl_chirality_pair_julia_results.json`; `system_v5/ops/formal_scouts/foundation_foundation_r5_weyl_chirality_pair_*`; `system_v5/julia_carrier/scratch_jax_snapshot_20260604/geometry_weyl_lr_gamma5_jax_results.json` | yes | JAX sheet-pair file has `all_pass: false`; Julia/JAX/PyTorch formal-scout legs appear to exist for Weyl chirality pair, but current inspected result is not a clean pass-backed tower rung | exists with mixed evidence | RERUN |
| G9 | loop classes fiber/base | `system_v7/sims/finite_ring_block_partition_reversible_qca_gnvw_index_v0/`; `system_v7/sims/finite_cycle_z_n_holonomy_section_lift_discriminator_v0/`; `system_v7/sims/ring_checkerboard_axis2_kt_holonomy_v0/`; `system_v5/julia_carrier/hopf_three_ways_*` | yes | julia, jax, pytorch in block-partition QCA agreement; exact-only holonomy discriminator also present | exists/runs with 3 legs for loop/index behavior | READY |
| G10 | the 8 terrain flows | `system_v7/sims/axis_relation_matrix_probe_v0/`; `system_v7/sims/type1_engine_v0/`; `system_v7/sims/axis0_terrain_engine_leap_v0/`; `system_v5/julia_carrier/wb_axis3_terrains_julia_results.json`; `system_v5/julia_carrier/scratch_jax_snapshot_20260604/wb_axis3_terrains_jax_results.json`; source extractions in `system_v7/sims/TYPE1_ENGINE_EXTRACTION_20260703.md` and `AXIS_RELATION_ALGEBRA_EXTRACTION_20260703.md` | yes | axis relation is Julia+NumPy; terrain leap envelope records Julia/JAX/PyTorch but JAX reads peer result and is fake terrain-grid scoped; Type 1 source-correct flow needs full 3-engine rerun | exists but not a clean 8-flow 3-engine rung | RERUN |
| G11 | nested shells/flux | `system_v5/julia_carrier/results/foundation_nested_hopf_weyl_signed_cut_ratchet_julia_results.json`; `system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_*`; `system_v5/julia_carrier/disc_shell_capacity_2n2_julia_results.json`; `system_v5/ops/formal_scouts/mp4_chemistry_hopf_shells_jax.py`; `system_v5/ops/formal_scouts/claude_integrated_manifold_modules/flux_conformal_projectors_and_floer_complexes.py`; `system_v6/sims/rpf_dual_chiral_engines_v0/` | yes | declared `all_three_full_sims` and `all_pass: true` in nested Hopf/Weyl/signed-cut ratchet result; several flux/shell pieces are Julia/JAX/support modules | exists/runs, but should be rerun fresh as part of assembled tower | READY |
| G12 | cut lattice | `system_v7/sims/cut_lattice_schmidt_entropy_v0/`; `system_v7/sims/manifold_L8_cut_lattice_gate2_a/`; `system_v7/sims/manifold_L8_cut_lattice_gate2_b/`; `system_v5/legos/bipartite_cut_mutual_conditional_coherent_information_pytorch_sympy_z3.py` | yes | julia, jax, pytorch plus exact result for `cut_lattice_schmidt_entropy_v0`; manifold L8 variants are Julia+NumPy | exists/runs with 3 legs | READY |
| G13 | Xi bridge | `system_v7/sims/DUAL_RATCHET_FORMALIZATION_XI_EXTRACTION_20260703.md`; `system_v7/sims/XI_CANDIDATE_TEST_SPECS_20260703.md`; `system_v5/julia_carrier/xi_shell_bridge_probe_julia_results.json`; `system_v5/julia_carrier/xi_shell_bridge_probe_jax_results.json` | yes | Julia and JAX only found; no PyTorch Xi leg and no closure result | intentionally open bridge | OPEN |

## Operator Ladder O0-O9

The operator ladder is partially implemented, but not assembled as one 3-engine ladder.

- O0 probes / O1 indistinguishability / O2 quotient: best covered by `distinguishability_quotient_floor_v0`, `finite_distinguishability_quotient_forced_or_installed_carrier_v0`, and `finite_probe_quotient_inverse_limit_tower_1q_through_4q`; these have 3-engine result sets.
- O3 survivor restrictions / O4 update operators: best covered by `independent_survivor_restriction_noncommutation_verify_v0`, `ordered_channel_maps_noncommutation_matrix_v0`, N01 Julia receipts, and survivor threshold sims.
- O5 density operator: density legos and `density_matrix_spinor_lift_*` exist, but the rho-first operator stage is not one all-three result.
- O6 spinor/Hopf operators: Hopf and spinor legos/Julia/JAX receipts exist, but are scattered.
- O7 sheet/chirality operators: Weyl sheet and chirality-pair evidence exists; inspected JAX sheet result has `all_pass: false`, so do not treat as ready.
- O8 terrain-flow operators: corrected Type 1 / axis relation evidence exists, mostly Julia+NumPy or scoped/fake terrain envelopes; rerun needed.
- O9 composed stages: `foundation_nested_hopf_weyl_signed_cut_ratchet_*`, `cut_lattice_schmidt_entropy_v0`, and `mp4_cosmological_constant_dissolves_*` compose stages, but composition should be rerun only after G5-G10 are reassembled.

## Entropy Ladder E0-E11

Entropy evidence exists at many layers, but the owner-corrected order matters: classical Shannon does not enter before the density-matrix rung. Treat pre-G5 entropy/counts only as class-count or finite-support diagnostics.

- E0 class-count / finite support: `finite_ring_checkerboard_support_three_presentation_consistency_v0`, `finite_support_topology_entropy_witness_*`.
- E1 quotient class counts: `distinguishability_quotient_floor_v0`, `finite_probe_quotient_inverse_limit_tower_1q_through_4q`.
- E2 survivor counts: survivor/noncommutation sims.
- E3 history/update entropy: ordered-channel and online-regime/update sims.
- E4 density/von Neumann family: `density_matrix_spinor_lift_*`, `spectral_entropy_family_density_state_pytorch_sympy_z3_results.json`, `qit_density_entropy_*`.
- E5 spinor/Hopf entropy readouts: Hopf/spinor receipts and legos.
- E6 sheet/chirality entropy: Weyl/chirality pair, gamma5 survivor quotient scouts.
- E7 loop/fiber/base entropy: QCA block partition and holonomy sims.
- E8 terrain-flow entropy: axis relation/type1 terrain evidence; rerun needed.
- E9 nested shell/flux entropy: nested Hopf/Weyl signed-cut and shell/flux scouts.
- E10 cut-lattice entropy: `cut_lattice_schmidt_entropy_v0` is the strongest current 3-engine anchor.
- E11 `Phi0` forms / Xi bridge: open; only candidate Xi Julia/JAX probes and specs found.

## Minimal Assembly Chain

Shortest current chain to instantiate G0 -> G12 end to end after fresh rerun on Julia/JAX/PyTorch:

1. `system_v7/sims/finite_ring_checkerboard_support_three_presentation_consistency_v0/` for G0 support, but add/rerun missing Julia/PyTorch legs or replace with a three-engine support sim.
2. `system_v7/sims/distinguishability_quotient_floor_v0/` for G1.
3. `system_v7/sims/finite_probe_quotient_inverse_limit_tower_1q_through_4q/` for G2.
4. `system_v7/sims/independent_survivor_restriction_noncommutation_verify_v0/` for G3.
5. `system_v7/sims/ordered_channel_maps_noncommutation_matrix_v0/` for G4.
6. Assemble a rho-first G5 from `system_v5/julia_carrier/density_matrix_spinor_lift_*` plus PyTorch density legos, or write a clean all-three `density_matrix_spinor_lift_v1` envelope.
7. Assemble G6/G7 from `clifford_spinor_carrier_rung`, `jax_clifford_spinor_carrier_smt`, `hopf_three_ways_*`, and PyTorch/geomstats Hopf lego into one spinor-Hopf all-three rung.
8. Rerun/fix G8 from `foundation_foundation_r5_weyl_chirality_pair_*` and `weyl_sheet_pair_probe_*`; do not use the current failing JAX sheet result as pass evidence.
9. `system_v7/sims/finite_ring_block_partition_reversible_qca_gnvw_index_v0/` for G9 loop/fiber/base classes.
10. Rerun/assemble G10 from `axis_relation_matrix_probe_v0`, `type1_engine_v0`, and corrected Type 1 source extractions into a true 8-terrain-flow three-engine rung.
11. `system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_*` / `system_v5/julia_carrier/results/foundation_nested_hopf_weyl_signed_cut_ratchet_julia_results.json` for G11 nested shells/flux, rerun fresh.
12. `system_v7/sims/cut_lattice_schmidt_entropy_v0/` for G12 cut lattice.

Minimal chain length: 12 sim packets/envelopes, because G5-G8/G10 need assembly or repair rather than being a single ready packet.

## Gap List Ranked By Tower Blockage

1. G5 rho-first all-three assembly is the biggest blocker: everything downstream is supposed to run on `rho`, and current evidence is split across Julia/JAX density lift plus PyTorch density legos.
2. G10 corrected 8 terrain flows is the next blocker: Type 1 source-correct material exists, but the clean all-three flow rung is not assembled.
3. G6-G7 spinor/Hopf all-three envelope is scattered: enough pieces exist to build it, but the tower needs one rerunnable rung.
4. G8 two-sheet `+/- H0` is mixed: a JAX sheet result is explicitly not passing, while formal-scout chirality-pair legs appear promising.
5. G0 finite support has good exact/JAX support but needs a clean Julia/JAX/PyTorch rerun to qualify as a 3-engine tower base.
6. G13 Xi bridge remains OPEN by design: candidate specs and Julia/JAX probes exist, but no closed 3-engine bridge result.

## Totals

- READY: 7 rungs (G1, G2, G3, G4, G9, G11, G12).
- RERUN: 6 rungs (G0, G5, G6, G7, G8, G10).
- GAP: 0 rungs found as total absence.
- OPEN: 1 rung (G13 Xi bridge).
