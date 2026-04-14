# Sim Corrections and Classifications

Date: 2026-04-05
Source: Hermes audit + Opus verification

---

## Corrections Applied

### 1. Torus entropy peak location

Earlier report: peak at η=0.687. Hermes correction: Clifford.
Verification: at 10 cycles η=0.76, at 200 cycles η=0.76.
Both are NEAR Clifford (0.79) but not exactly on it.
50-cycle run showed anomalous peak at outer edge.

STATUS: Clifford is the long-run attractor for the entropy peak,
but convergence is not monotonic. Treat η≈0.76-0.79 as the peak
region, not a single point.

### 2. Swapped inductive↔deductive order

Earlier report: C = 0.040 (10 cycles). Hermes said: C = 0.000.
Verification: C = 0.040 at 10 cycles, C = 0.013 at 20 cycles.
Not zero — severely degraded but not fully killed.

STATUS: The earlier 0.040 was a short-run transient. At 20 cycles
it drops to 0.013 (0.16× baseline). Label earlier measurement as
"10-cycle transient." Current best value: 0.013 at 20 cycles.

### 3. Gudhi persistent homology

Betti_1 = 0 for long trajectories. Type 2 has one finite-persistence
H1 interval but no true persistent loop. Do not describe trajectories
as closed loops.

---

## Sim Classification

### Canonical Evidence (load-bearing, verified positive + negative)

| File | What it proves |
|---|---|
| layer0_root_constraints_results.json | F01+N01 verified, commutative kills C |
| layer1_admissibility_fences_results.json | 15/15 fences, all violations kill |
| layer2_carrier_realization_results.json | C², S³, Hopf all verified |
| layer3_connection_loop_geometry_results.json | Fiber stationary, base traversing |
| layer4_weyl_chirality_results.json | L/R anti-aligned, max distinguishable |
| layer5_four_topologies_results.json | 4 forced by su(2), all necessary |
| negative_sim_battery_results.json | 12 ablations: 6 killed, 4 severely hit |
| gauge_group_correspondence_results.json | su(2)×u(1) = electroweak |
| engine_earned_entanglement_results.json | T1 accumulates, T2 dissipates |
| per_stage_entanglement_dynamics_results.json | Fi = only builder |
| ratchet_irreversibility_results.json | Never returns to initial |

### Good Evidence (verified but not yet layered)

| File | What it shows |
|---|---|
| bridge_family_live_test_results.json | Bell mixing threshold p=0.60 |
| multi_torus_transport_results.json | Transport trades entropy for entanglement |
| dual_stack_ratchet_comparison_results.json | Dual = constrained accumulation |
| comprehensive_preaxis_state_results.json | 10 confirmed, 5 open, 3 killed |
| strength_resonance_sweep_results.json | Goldilocks zone: T1@0.825, T2@0.575 |
| loop_order_sensitivity_results.json | Order IS load-bearing (N01) |
| ax5_entanglement_split_results.json | F-kernel generates, T-kernel structures |
| dual_stack_200cycle_oscillation_results.json | ~50 cycle period, recurring peaks |

### Diagnostic Only (informational, not evidence)

| File | Why |
|---|---|
| full_tool_integration_results.json | Tool verification, not physics |
| deep_tool_integration_results.json | Tool verification |
| integrated_multi_tool_results.json | Tool verification |
| active_clifford_driven_results.json | Bridge testing |
| pimono_smoke_test_output.json | Infrastructure test |
| simultaneous_preaxis_surface_probe_results.json | Snapshot, not systematic |

### Legacy / Superseded

| File | Superseded by |
|---|---|
| Earlier torus peak at η=0.687 | Verified: peak at η≈0.76-0.79 (near Clifford) |
| Earlier swapped-order C=0.040 | Verified: 10-cycle transient, drops to 0.013 at 20 cycles |
| history_vs_pointwise_ax0_results.json | Superseded by bridge_family_live_test |
| hopf_pointwise_pullback_results.json | Confirmed trivial; superseded by geometry survey |

### Blocked / Awaiting Prerequisites

| What | Blocked on |
|---|---|
| Axis 0 I_c > 0 | Bridge construction (layer 15) |
| Shell-cut I_c positive | Larger Hilbert space or entangling channel |
| su(3) gauge group | dim(H) ≥ 3 required |
