# Sim Session Index — 2026-04-05

All sims run this session with findings. Each result is a JSON file
in system_v4/probes/a2_state/sim_results/.

---

## Scope and Boundary

This doc is a dated session snapshot.
It is useful for recovering what the 2026-04-05 batch actually ran and found.

This doc is not the primary surface for:
- current live repo truth across later reruns
- promotion status by resolution layer
- final canonical summaries of what remains open

Use it with:
- `TIER_STATUS.md` for current status framing
- `SIM_CORRECTIONS_AND_CLASSIFICATIONS.md` for follow-on corrections
- the underlying result JSON files when making strong claims

Short rule:
- this file tells you what that session produced
- it does not automatically tell you what is still true now

## Falsification Sims (designed from tradition mapping mismatches)

| # | Sim | Result file | Key finding |
|---|---|---|---|
| 1 | Gauge group correspondence | gauge_group_correspondence_results.json | Engine generates su(2)×u(1) = electroweak. Missing su(3). |
| 2 | Viability vs attractor | viability_vs_attractor_results.json | MIXED — clusters (attractor-like) but perturbation diverges (viability-like). |
| 3 | Metric uniqueness | metric_uniqueness_results.json | Type 1: perfect agreement. Type 2: high but not perfect (0.88-0.95). |

## Structural Sims

| # | Sim | Result file | Key finding |
|---|---|---|---|
| 4 | Feedback loop coupling | feedback_loop_coupling_results.json | 18 sign changes per 40 stages. Cooling-heating anti-correlated (-0.29). |
| 5 | Chirality mirror symmetry | chirality_mirror_symmetry_results.json | NOT a simple L↔R mirror. Cross-distances larger than same-side. |
| 6 | Power law vs bell curve | power_law_vs_bell_curve_results.json | Intermediate — neither pure bell curve nor pure power law. |
| 7 | Dual-stack necessity | dual_stack_necessity_results.json | Interleaved T1+T2 produces 30× more state diversity. |
| 8 | Berry phase torus ladder | berry_phase_torus_ladder_results.json | Varies strongly (std ~1.56). Non-trivial holonomy. |

## Pre-Axis Geometry Sims

| # | Sim | Result file | Key finding |
|---|---|---|---|
| 9 | Simultaneous surface probe | simultaneous_preaxis_surface_probe_results.json | All resolution layers consistent on same state. Te/Fi zero at Clifford [1,0,0]. |
| 10 | Full geometry survey | full_preaxis_geometry_survey_results.json | Clifford torus = persistent entropy max. Symmetric gradient. I_c crosses zero for T1. |

## Entanglement Sims

| # | Sim | Result file | Key finding |
|---|---|---|---|
| 11 | Entanglement structure survey | entanglement_structure_survey_results.json | Clifford has 5-85× more entanglement. I_c always negative. |
| 12 | Bridge family live test | bridge_family_live_test_results.json | Chiral bridge I_c=+1.0 (injected). Bell mixing threshold p=0.60. |
| 13 | Engine earned entanglement | engine_earned_entanglement_results.json | Type 1 GROWS C (0.038→0.112). Type 2 DECAYS to 0 by 50 cycles. |
| 14 | Per-stage dynamics | per_stage_entanglement_dynamics_results.json | Fi is ONLY builder (+0.039). Te strongest destroyer (-0.018). |
| 15 | Ax5 entanglement split | ax5_entanglement_split_results.json | T-kernel: C=0, S=0.56. F-kernel: C=0.024, S=0.52. Full: C=0.059, S=0.38. |

## Operator/Composition Sims

| # | Sim | Result file | Key finding |
|---|---|---|---|
| 16 | Loop order sensitivity | loop_order_sensitivity_results.json | Random order → C=0.013. Normal → 0.059. Order IS load-bearing (N01). |
| 17 | Geometric ablation battery | geometric_ablation_battery_results.json | p=0 kills C. p=1 kills C. Goldilocks zone. Inner/outer = 0.72× baseline. |
| 18 | Strength resonance sweep | strength_resonance_sweep_results.json | T1 peak at p=0.825 (C=0.162). T2 peak at p=0.575 (C=0.039). |
| 19 | Optimal dual-stack | optimal_dual_stack_results.json | T1 loses C in alternation. T2 maintains ~0.035. Structural, not tunable. |

## Tool Integration Sims

| # | Sim | Result file | Key finding |
|---|---|---|---|
| 20 | Integrated multi-tool | integrated_multi_tool_results.json | All 4 tools (clifford/TopoNetX/PyG/z3) consistent on same state. |
| 21 | Active Clifford-driven | active_clifford_driven_results.json | 7/8 stages match (Td<0.06). N01 confirmed on cross-axis pairs. |
| 22 | Deep tool integration | deep_tool_integration_results.json | 10 tools all producing real results on engine. |
| 23 | Full tool integration | full_tool_integration_results.json | su(2) proven exactly. Pydantic contracts. All 9 tools verified. |

---

## Summary of Key Findings

1. The engine generates su(2)×u(1) (electroweak algebra)
2. Clifford torus is the entropy AND entanglement maximum
3. Fi is the ONLY entanglement builder; all others destroy
4. Type 1 accumulates entanglement; Type 2 dissipates it
5. Composition order is load-bearing for entanglement (N01)
6. Operator strength has a Goldilocks zone (not too weak, not too strong)
7. The two chiralities have different optimal strengths
8. Bridge layer is needed for I_c > 0 (quantum advantage)
9. Bell mixing threshold is p=0.60
10. The dual-stack entanglement pattern is structural, not tunable

---

## Tool Bridges Created

| Bridge | File | Status |
|---|---|---|
| Clifford Cl(3) | clifford_engine_bridge.py | Roundtrips verified |
| TopoNetX cell complex | toponetx_torus_bridge.py | 24v/40e/16f complex |
| PyG HeteroData | pyg_engine_bridge.py | Typed graph with live state |
| z3 fences | Direct z3 calls | All 7 BC fences enforced |

---

## Sim Results Consolidated

| Location | Count |
|---|---|
| Main results | 256 |
| LevRatchet legacy | 62 (in levratchet_legacy/) |
| A1 fuel sims | 65 (in a1_fuel_sims/) |
| Total | 383 |
