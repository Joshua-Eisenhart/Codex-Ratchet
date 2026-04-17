---
title: Probe Doc Result Map
created: 2026-04-09
updated: 2026-04-16
type: concept
tags: [system, audit, simulation, reference, status, validation]
sources:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/actual_lego_normalization_queue.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/17_actual_lego_registry.md
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/SIM_SESSION_INDEX.md
framing: current
---

# Probe-Documentation-Result Bridge Map

Maps the operational bridge: wiki concept page → source probe file → result JSON → maturity/status. This is the machine-facing link between documentation and actual sim evidence.

## How to Read This

Each row: **Concept** | **Wiki page** | **Probe file** | **Result JSON** | **Status**

Status terms (per [[llm-controller-contract]]):
- `exists` — file on disk
- `runs` — executes without error
- `passes local rerun` — fresh run confirms expected tests pass
- `canonical by process` — passes local rerun + SIM_TEMPLATE + tool manifest + classification
- `artifact-side classification: canonical` — the result JSON self-classifies as `canonical`, but this page is not independently asserting the full process gate

## Higher-maturity sims in this snapshot

| Concept | Wiki page | Probe | Result | Status |
|---|---|---|---|---|
| Phase 7 baseline validation | [[pytorch-ratchet-build-plan]] | sim_phase7_baseline_validation.py | phase7_baseline_validation_results.json | passes local rerun (C1/C3/C4) |
| Edge state writeback | [[migration-registry]] | sim_edge_state_writeback.py | edge_state_writeback_results.json | passes local rerun |
| Entanglement witness (C1) | [[entanglement-theory]] | sim_c1_entanglement_object_search.py | c1_entanglement_object_search_results.json | passes local rerun |
| Entropy structure (C2) | [[entropy-sweep-protocol]] | sim_c2_entropy_structure_search.py | c2_entropy_structure_search_results.json | passes local rerun |
| Geometric engine | [[geometry-ingredient-map]] | engine_geometric.py | geometric_engine_results.json | runs |
| Graph-driven engine | [[pytorch-ratchet-build-plan]] | engine_graph_driven.py | (writes to a2_state/) | runs |

## Geometry sims with cited artifact presence

| Concept | Wiki page | Probe | Result | Status |
|---|---|---|---|---|
| Hopf torus lego | [[hopf-fibration-mathematics]] | sim_hopf_torus_lego.py | hopf_torus_lego_results.json | exists |
| Fubini-Study geometry | [[quantum-geometry-fubini-study]] | sim_fubini_study_geometry.py | fubini_study_geometry_results.json | exists |
| Bures geometry | [[distance-metrics-state-space]] | sim_bures_geometry.py | bures_geometry_results.json | exists |
| Berry phase (torus ladder) | [[berry-phase-and-holonomy]] | sim_axis_hopf_geometry.py | axis_hopf_geometry_results.json | exists |
| Berry curvature (Stokes) | [[berry-phase-and-holonomy]] | sim_pure_lego_berry_curvature_stokes.py | berry_curvature_stokes_results.json | exists |
| Riemannian curvature | [[geometry-ingredient-map]] | sim_pure_lego_riemannian_curvature.py | riemannian_curvature_results.json | exists |
| Contact structure S³ | [[geometry-ingredient-map]] | sim_contact_structure_s3.py | contact_structure_s3_results.json | exists |
| QFI kill-point divergence | [[geometry-ingredient-map]] | sim_pure_lego_qfi_killpoint_divergence.py | qfi_killpoint_divergence_results.json | exists |
| Clifford algebra | [[clifford-algebra-qit]] | sim_clifford_generator_basis.py | clifford_generator_basis_results.json | exists |
| Weyl chirality | [[clifford-algebra-qit]] | sim_weyl_geometry_ladder_audit.py | weyl_geometry_ladder_audit_results.json | exists |

## Bridge / Entropy Sims

| Concept | Wiki page | Probe | Result | Status |
|---|---|---|---|---|
| Xi bridge bakeoff | [[qit-engine-geometry-entropy-bridge]] | sim_xi_bridge_bakeoff.py | xi_bridge_bakeoff_results.json | exists |
| Phi0 kernel discriminator | [[qit-engine-geometry-entropy-bridge]] | sim_a0_kernel_discriminator.py | a0_kernel_discriminator_results.json | exists |
| Axis 0 gradient | [[pytorch-ratchet-build-plan]] | axis0_gradient_sim.py + sim_torch_axis0_gradient.py + sim_bridge_axis0_gradient_autograd.py | axis0_gradient_results.json + torch_axis0_gradient_results.json + bridge_axis0_gradient_autograd_results.json | exists |
| Hopf pointwise pullback | [[qit-engine-geometry-entropy-bridge]] | sim_hopf_pointwise_pullback.py | hopf_pointwise_pullback_results.json | exists |
| Fiber/base transport | [[qit-engine-geometry-entropy-bridge]] | sim_fiber_base_transport_test.py | fiber_base_transport_test_results.json | exists |


## Thermodynamics / Viability / Basin Sims

| Concept | Wiki page | Probe | Result | Status |
|---|---|---|---|---|
| Pure quantum thermodynamics | [[stochastic-thermodynamics-reference]] | sim_pure_lego_quantum_thermodynamics.py | pure_lego_quantum_thermodynamics_results.json | artifact shows `all_pass: true`; no classification field |
| Strong-coupling Landauer bookkeeping | [[stochastic-thermodynamics-reference]] | sim_qit_strong_coupling_landauer.py | qit_strong_coupling_landauer_results.json | artifact-side classification: `canonical` |
| Carnot runtime negative result | [[stochastic-thermodynamics-reference]] | sim_carnot_gradient_bound.py | carnot_gradient_bound_validation.json | artifact-side `classification: classical_baseline`; checked row supports a negative result at the tested parameterization |
| QIT Carnot two-bath cycle | [[stochastic-thermodynamics-reference]] | sim_qit_carnot_two_bath_cycle.py | qit_carnot_two_bath_cycle_results.json | exists |
| QIT Carnot finite-time companion | [[stochastic-thermodynamics-reference]] | sim_qit_carnot_finite_time_companion.py | qit_carnot_finite_time_companion_results.json | exists |
| QIT Carnot hold-policy companion | [[stochastic-thermodynamics-reference]] | sim_qit_carnot_hold_policy_companion.py | qit_carnot_hold_policy_companion_results.json | exists |
| QIT Szilard-Landauer cycle | [[stochastic-thermodynamics-reference]] | sim_qit_szilard_landauer_cycle.py | qit_szilard_landauer_cycle_results.json | exists (self-classified canonical on disk; public process promotion remains under re-audit) |
| QIT Szilard record companion | [[stochastic-thermodynamics-reference]] | sim_qit_szilard_record_companion.py | qit_szilard_record_companion_results.json | exists |
| QIT Szilard substep companion | [[stochastic-thermodynamics-reference]] | sim_qit_szilard_substep_companion.py | qit_szilard_substep_companion_results.json | exists |
| Maxwell demon sidecar | [[stochastic-thermodynamics-reference]] | demon_fixed_sim.py | demon_fixed_results.json | passes local rerun (supporting sidecar) |
| Szilard super-additivity | [[stochastic-thermodynamics-reference]] | szilard_64stage_v2_sim.py | szilard_64stage_v2_results.json | exists (exploratory evidence) |
| Stochastic double-well Landauer erasure | [[stochastic-thermodynamics-reference]] | sim_stoch_doublewell_landauer_erasure.py | stoch_doublewell_landauer_erasure_results.json | exists |
| Stochastic harmonic Carnot cycle | [[stochastic-thermodynamics-reference]] | sim_stoch_harmonic_carnot_cycle.py | stoch_harmonic_carnot_cycle_results.json | exists |
| Engine-lab comparison matrix | [[stochastic-thermodynamics-reference]] | sim_engine_lab_matrix.py | engine_lab_matrix_results.json | exists |
| QIT Moloch coordination trap | [[moloch-trap-reference]] | sim_qit_moloch_coordination_trap.py | qit_moloch_coordination_trap_results.json | artifact-side classification: `canonical` |
| QIT predictive world model | [[qit-ai-foundations-bridge]] | sim_qit_predictive_world_model.py | qit_predictive_world_model_results.json | artifact-side classification: `canonical` |
| Viability vs attractor | [[attractor-basins-formal-reference]] | sim_viability_vs_attractor.py | viability_vs_attractor_results.json | artifact-side classification: `canonical` |
| Axis0 basin boundary | [[attractor-basins-formal-reference]] | sim_axis0_attractor_basin_boundary.py | axis0_attractor_basin_boundary_results.json | artifact-side `classification: classical_baseline` |
| QIT attractor basin recovery | [[attractor-basins-formal-reference]] | sim_qit_attractor_basin_recovery.py | qit_attractor_basin_recovery_results.json | artifact-side classification: `canonical` |

## Engine Files

| Engine | Role | Status |
|---|---|---|
| engine_geometric.py | Spinor-first geometry engine | runs |
| engine_graph_driven.py | Graph/TopoNetX transport gate | runs |
| engine_core.py | Core simulation engine | exists |
| engine_pure_clifford.py | Clifford algebra engine | exists |
| engine_unified.py | Unified engine | exists |
| engine_pyg_message_passing.py | PyG message passing | exists |
| engine_toponetx_constrained.py | TopoNetX constrained | exists |

## Status Gaps (documented but not simed, or simed but not documented)

### Canonical gaps still open
- Engine-side Szilard interpretations beyond the bounded finite bookkeeping row are still exploratory; super-additivity, record-lifetime, and substep bookkeeping surfaces are not yet promoted to canonical engine doctrine.
- Legacy Moloch surfaces remain split: `igt_moloch_trap_sim.py` is still older exploratory evidence, and `sim_moloch_trap_field.py` currently disagrees with its own strongest classical-collapse claim. The new bounded QIT Moloch row is the owner surface for now.
- Kernel-method support exists, but Qiskit-style quantum-kernel tooling is still supporting-only and not part of the main thermodynamics or basin evidence stack.

### Simed, no dedicated wiki page
- contact_structure_s3 → needs [[contact-structure-s3]]
- riemannian_curvature → needs [[riemannian-curvature]]
- qfi_killpoint_divergence → needs [[qfi-killpoint-behavior]]
- pure_lego_symplectic_kahler_weyl → partially in [[clifford-algebra-qit]]
- nested_torus_geometry → partially in [[hopf-fibration-mathematics]]

## Related Pages

- [[geometry-ingredient-map]] — what geometric ingredients exist
- [[docs-vs-sims-gap-audit]] — gap tracking between docs and sims
- [[pytorch-ratchet-build-plan]] — the build plan
- [[migration-registry]] — per-family migration state
- [[llm-controller-contract]] — status label definitions
- [[enforcement-and-process-rules]] — what canonical means
- [[current-canonical-spine]] — second-layer router for ordered loading
