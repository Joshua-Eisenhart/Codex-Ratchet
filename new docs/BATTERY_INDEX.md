# Negative Battery Index

## Document Status
| Field | Value |
|-------|-------|
| **last_verified** | 2026-04-07 |
| **status** | Machine-generated from repo scan. Counts are discovered, not prescribed. |

## Purpose
Authoritative index of all negative batteries in the project. Referenced by ENFORCEMENT_AND_PROCESS_RULES.md.

All paths are relative to `system_v4/probes/`. Result JSONs live in `a2_state/sim_results/`.

---

## Graveyard Batteries (Engine-Level Kill Tests)

These batteries run the engine with deliberately broken constraints and verify KILL outcomes.

### 1. Information Graveyard Battery
| Field | Value |
|-------|-------|
| **Source** | `information_graveyard_battery.py` |
| **Results** | `info_graveyard_results.json` |
| **Tests** | 8 |
| **Killed** | 8/8 |
| **Layer** | L0-L2 (root constraints, CPTP, operator necessity) |
| **Status** | Active |

**Failure modes tested:** NEG-CLASSICAL (diagonal-only channel), NEG-NO_FEEDBACK (open-loop), NEG-DETERMINISTIC (no stochastic element), NEG-MAX_MIXED (I/d start), NEG-IDENTICAL_OP (all operators same), NEG-PROJ_ONLY (projection only), NEG-FROZEN_BASIS (no rotation), NEG-ANTI_RATCHET (systematic phi decrease).

### 2. Deep Graveyard Battery
| Field | Value |
|-------|-------|
| **Source** | `deep_graveyard_battery.py` |
| **Results** | `deep_graveyard_results.json` |
| **Tests** | 8 |
| **Killed** | 8/8 |
| **Layer** | L0-L4 (CPTP, chirality, operator necessity, compound constraints) |
| **Status** | Active |

**Failure modes tested:** NEG-C3 (CPTP violation), NEG-X2 (chirality swap L/R), NEG-Ti (no measurement), NEG-Te (no unitary drive), NEG-Fi (no spectral projection), NEG-C4 (force identity), CMP-1 (F01+N01 compound), CMP-2 (C6+C8 compound).

### 3. Extended Graveyard Battery
| Field | Value |
|-------|-------|
| **Source** | `extended_graveyard_battery.py` |
| **Results** | `extended_graveyard_results.json` |
| **Tests** | 6 |
| **Killed** | 6/6 |
| **Layer** | L0-L4 (CPTP, monotonicity, chirality, sequence ordering) |
| **Status** | Active |

**Failure modes tested:** CMP-3 (C3+C5 entropy ordering), CMP-4 (F01+N01+C3 triple lock), CMP-5 (C6+X2 dual-loop+chirality), NEG-SCRAMBLE (random stage ordering), NEG-SYMMETRIC (force self-adjoint ops), NEG-DECOHERE (maximal decoherence every stage).

### 4. Thermodynamic Graveyard Battery
| Field | Value |
|-------|-------|
| **Source** | `thermodynamic_graveyard_battery.py` |
| **Results** | `thermo_graveyard_results.json` |
| **Tests** | 8 |
| **Killed** | 8/8 |
| **Layer** | L0-L3 (finitude, environmental coupling, thermodynamic laws) |
| **Status** | Active |

**Failure modes tested:** NEG-CLONE (no-cloning violation), NEG-ZERO_H (zero Hamiltonian), NEG-INF_GAMMA (infinite coupling), NEG-PURE_LOCK (pure state no dissipation), NEG-DIM1 (trivial Hilbert space d=1), NEG-NO_BATH (no environment), NEG-ZERO_TEMP (third law violation), NEG-REVERSED (entropy pumped inward).

### 5. Entropy Form Negative Battery
| Field | Value |
|-------|-------|
| **Source** | `entropy_form_negative_battery.py` |
| **Results** | `entropy_form_negative_battery_results.json` |
| **Tests** | 16 comparisons across 6 entropy alternatives |
| **Layer** | L0-L1 (entropy form selection, basis safety) |
| **Status** | Active |

**What it tests:** Whether any alternative entropy (linear, Renyi-2, Tsallis-2, Shannon-diagonal, relative-to-maxmix, conditional proxy) outperforms von Neumann for the Hopf/Weyl engine regime. Confirms vN remains the best default. Shannon-diagonal is not geometry-safe. Conditional entropy not meaningful without joint 4x4 rho_LR.

---

## Pure Math Negative Batteries (No Engine Dependency)

These test failure modes of quantum-information primitives directly, independent of the engine.

### 6. Negative Geometry Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_negative_geometry.py` |
| **Results** | `negative_geometry_results.json` |
| **Tests** | 10 |
| **Layer** | L0-L2 (geometric primitives: Fubini-Study, Bures, Cl(3) rotors) |
| **Status** | Active |

**Failure modes tested:** Quantum-geometric quantities that break due to numerical noise, domain violations, or topological edge cases. Tests Fubini-Study, Bures distance, Cl(3) rotor algebra boundary conditions.

### 7. Negative Density Matrix Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_negative_density_matrices.py` |
| **Results** | `negative_density_matrix_battery_results.json` |
| **Tests** | 12 |
| **Layer** | L0 (density matrix validity, CPTP prerequisites) |
| **Status** | Active |

**Failure modes tested:** Non-Hermitian input, negative eigenvalue, wrong trace, rank deficiency, numerical precision, dimension mismatch, near-singular states, non-CP map (partial transpose), z3 proof (no valid DM with negative eigenvalue), concurrence on non-PSD, mixed pathologies, anti-unitary channel.

### 8. Negative Topology Graphs Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_negative_topology_graphs.py` |
| **Results** | `negative_topology_graphs_results.json` |
| **Tests** | 10 |
| **Layer** | L2-L5 (cell complexes, Hodge Laplacian, PyG message passing) |
| **Status** | Active |

**Failure modes tested:** 0-vertex cell complex, dangling edge, invalid B2*B1, Klein bottle vs torus Euler characteristic, disconnected graph Betti, K1 trivial graph, self-loop in PyG, negative edge weights, isolated nodes, overlapping faces.

### 9. Negative Channels Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_negative_channels.py` |
| **Results** | `negative_channels_results.json` |
| **Tests** | 10 |
| **Layer** | L0-L1 (CPTP channel validity) |
| **Status** | Active |

**Failure modes tested:** Partial transpose, universal NOT, trace-increasing map, non-Hermitian output, depolarizing p>1, amplitude damping gamma>1, dephasing composition, zero Kraus, z3 proof (positive-not-CP), contractivity violation.

### 10. Negative Entanglement Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_negative_entanglement.py` |
| **Results** | `negative_entanglement_battery_results.json` |
| **Tests** | 10 |
| **Layer** | L0-L3 (entanglement measures and witnesses) |
| **Status** | Active |

**Failure modes tested:** Entanglement measure failures -- concurrence, negativity, witness operators, distillation preconditions.

### 11. Negative Compound Failures Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_negative_compound_failures.py` |
| **Results** | `negative_compound_failures_results.json` |
| **Tests** | 10 |
| **Layer** | L1-L5 (composition of legos: numerical error compounding) |
| **Status** | Active |

**Failure modes tested:** Iterated channel entropy accumulation, concurrence of SIC-POVM-reconstructed state, Berry phase after low-rank compression, QFI through 50 dephasing channels, teleportation with Werner state, discord after distillation, steering ellipsoid after non-CP map, relative entropy of near-identical states, eigenvalue interlacing after non-TP map, MPS bond dimension after CNOT.

### 12. Negative Entropy Boundaries Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_negative_entropy_boundaries.py` |
| **Results** | `negative_entropy_boundaries_results.json` |
| **Tests** | 10 |
| **Layer** | L0-L1 (entropy measure boundary conditions) |
| **Status** | Active |

**Failure modes tested:** vN entropy pure-state noise, Renyi edge cases (alpha<0, alpha=0, alpha->1), relative entropy support mismatch, conditional entropy for max-entangled, MI for product state, Tsallis->min-entropy convergence, linear entropy dimension scaling, rank boundary, non-density-matrix input, Shannon vs vN disagreement.

### 13. Negative Boundary Sweep Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_negative_boundary_sweep.py` |
| **Results** | `negative_boundary_sweep_results.json` |
| **Tests** | 10 |
| **Layer** | L0-L3 (exact transition boundaries via binary search) |
| **Status** | Active |

**Failure modes tested:** Exact parameter thresholds for concurrence (Werner p=1/3), negativity (p=1/3), Bell-CHSH (p=1/sqrt(2)), steering (p=1/sqrt(3)), discord (any p>0), QFI witness, depolarizing capacity, amplitude damping (gamma=1/2), teleportation fidelity (p=1/2), Schumacher compression rate.

### 14. Negative MEGA Boundaries Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_negative_mega_boundaries.py` |
| **Results** | `negative_mega_boundaries_results.json` |
| **Tests** | 15 |
| **Layer** | L0-L5 (advanced numerical boundary conditions) |
| **Status** | Active |

**Failure modes tested:** Purity boundary for discord, channel composition depth to max-mixed, eigenvalue precision gap, fidelity vs trace distance noise floor, entanglement near threshold (Werner), Berry phase small solid-angle, QFI low-signal, Kraus operator count vs numerical rank, partial trace dimension scaling, relative entropy asymmetry, concurrence vs negativity disagreement, MI strong subadditivity, channel fixed-point uniqueness, tomography sample complexity, compression loss vs entanglement.

### 15. Negative Advanced Legos Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_negative_advanced_legos.py` |
| **Results** | `negative_advanced_legos_results.json` |
| **Tests** | 10 |
| **Layer** | L1-L5 (advanced lego precondition failures) |
| **Status** | Active |

**Failure modes tested:** Teleportation with separable state, quantum walk on disconnected graph, integrable spacing fed to GUE classifier, Schumacher below entropy, MPS chi=1 for entangled state, stabilizer rank of Haar-random, distillation from separable state, BB84 with eavesdropper, CNOT cloning attempt, f-divergence triviality.

---

## Constraint Cascade and Cross-Layer Batteries

### 16. Negative Constraint Cascade Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_negative_constraint_cascade.py` |
| **Results** | `negative_constraint_cascade_results.json` |
| **Tests** | 10 |
| **Layer** | L0-L7 (cascade propagation of constraint violations) |
| **Status** | Active |

**What it tests:** Breaks one constraint at a time and measures how the violation propagates through the full L0-L7 stack.

### 17. Cross-Layer Negative Propagation Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_cross_layer_negative_propagation.py` |
| **Results** | `cross_layer_negative_propagation_results.json` |
| **Tests** | 13 breaks |
| **Layer** | L2-L12 (inter-layer dependency mapping) |
| **Status** | Active |

**Breaks tested:** L2 real-only, L4 no-chirality, L5 remove-Se, L7 random-order, L8 same-polarity, and 8 others. Maps which downstream layers fail when an upstream layer is broken.

### 18. Z3 Fence Exhaustive Negatives Battery
| Field | Value |
|-------|-------|
| **Source** | `sim_z3_fence_exhaustive_negatives.py` |
| **Results** | `z3_fence_exhaustive_negatives_results.json` |
| **Tests** | 120 (15 single-removal + 105 pair-removal) |
| **Fences** | 15 total |
| **Layer** | L0-L1 (admissibility fence necessity, z3 formal proofs) |
| **Status** | Active |

**What it tests:** For each of 15 admissibility fences, proves via z3 SMT that removing any single fence or any pair of fences admits a previously forbidden state. Exhaustive combinatorial coverage.

---

## Engine Negative SIMs (Specific Axiom Kill Tests)

These target individual axioms or structural properties of the engine.

### 19. neg_classical_probability_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 1 scenario, 10 trials | L0 (N01) | Classical-only probability (no coherence) cannot replicate 8-stage ratchet |

### 20. neg_commutative_engine_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 1 scenario, multi-trial | L0 (N01) | Commutative operators stall the engine |

### 21. neg_commutative_process_cycle_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 1 scenario, multi-trial | L0 (N01) | Commutative process cycle stalls |

### 22. neg_infinite_d_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 6 dimensions (d=2,4,8,16,32,64) | L0 (F01) | Performance degrades as d grows; finitude is necessary |

### 23. neg_single_loop_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 1 scenario, 10 trials | L3 (C6) | Single loop (FeTi only) saturates; dual-loop is necessary |

### 24. neg_no_dissipation_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 1 scenario, 10 trials | L3 (Fe necessity) | Without Fe, thermal death is mandatory |

### 25. neg_inverted_major_loop_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| Multi-trial | L3-L4 (sequence ordering) | Inverting Ti/Fe order destroys constraint accumulation |

### 26. neg_scrambled_sequence_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| Multi-trial, random permutations | L3-L4 (sequence ordering) | Random stage ordering stalls the engine |

---

## Geometry Negative SIMs (Hopf/Weyl/Torus Structure Tests)

### 27. sim_neg_axis0_frozen.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 1 comparison (adaptive vs frozen) | L6-L7 (Axis 0 necessity) | Axis 0 is load-bearing; freezing it degrades trajectory |

### 28. sim_neg_no_chirality.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 1 comparison (chiral vs flat) | L4 (chirality necessity) | Removing L/R Weyl divergence collapses the engine |

### 29. sim_neg_no_torus_transport.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 1 comparison (transport vs clamped) | L5 (torus control) | Clamping torus to Clifford degrades trajectory |

### 30. sim_neg_torus_scrambled.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 1 comparison (structured vs random schedule) | L5 (torus ordering) | Random torus schedule degrades coherence |

### 31. sim_neg_loop_law_swap.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| Multi-carrier comparison | L5 (loop law assignment) | Swapping fiber/base law roles fails on same carrier |

### 32. sim_neg_transport_delta_joint_ablation.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 4 conditions x multi-carrier | L4-L5 (joint chirality + loop-law) | Both chirality and loop-law must be present together |

---

## Stage Matrix Negative SIMs

These use `stage_matrix_neg_lib.py` as shared infrastructure and test per-stage structural properties across all 64 engine stages.

### 33. neg_missing_operator_stage_matrix_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 4 operators x 64 stages x 4 trials = 1024 | L3 (operator necessity per stage) | Dropping any single operator from a stage changes the outcome |

### 34. neg_native_only_stage_matrix_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 64 stages x 4 trials = 256 | L3 (operator diversity) | Collapsing to native-only operator is not equivalent to full 4-subcycle |

### 35. neg_type_flatten_stage_matrix_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 64 stages x 4 trials = 256 | L3-L4 (type-specific weighting) | Flattening type1/type2 weighting changes the stage matrix |

### 36. neg_axis6_shared_stage_matrix_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 14 mixed variants x 64 stages x 4 trials | L6 (Axis 6 per-stage polarity) | Mixed Axis 6 polarity within a stage produces different results |

### 37. neg_missing_fe_stage_matrix_sim.py
| Tests | Layer | What it kills |
|-------|-------|---------------|
| 64 stages x 4 trials = 256 | L3 (Fe necessity per stage) | Focused Fe-omission probe with rich metrics beyond trace distance |

---

## Original Engine Negative Battery

### 38. Negative SIM Battery (Original)
| Field | Value |
|-------|-------|
| **Source** | (generated by engine sweep, no single source file) |
| **Results** | `negative_sim_battery_results.json` |
| **Tests** | 12 |
| **Layer** | L3-L6 (engine parameter sweeps) |
| **Status** | Active |

**Failure modes tested:** neg_zero_strength, neg_max_strength, neg_random_order, neg_reversed_order, neg_flat_order, neg_degenerate_torus, neg_outer_only, neg_inner_only, neg_swapped_ind_ded, neg_wrong_chirality_order, neg_maxmix_init, neg_no_axis0.

---

## Summary Table

| Category | Batteries | Total Tests/Failure Modes |
|----------|-----------|--------------------------|
| Graveyard (engine kill) | 5 | 46 |
| Pure math (no engine) | 10 | 107 |
| Cascade / cross-layer | 3 | 143 |
| Engine axiom kills (neg_*) | 8 | ~40 (multi-trial each) |
| Geometry negatives (sim_neg_*) | 6 | ~12 (multi-carrier each) |
| Stage matrix negatives | 5 | ~1,792+ (64 stages x trials) |
| Original engine battery | 1 | 12 |
| **TOTAL** | **38 batteries** | **~2,152+ distinct failure-mode evaluations** |

### Coverage by Constraint Layer

| Layer | Description | Batteries Touching This Layer |
|-------|-------------|-------------------------------|
| L0 | Root constraints (F01, N01), density matrix validity | 1-5, 6-7, 9-10, 12-13, 16, 18, 19-22 |
| L1 | Admissibility fences, entropy forms, CPTP | 2-5, 9, 11-12, 15, 18 |
| L2 | Carrier realization, geometric primitives | 1-2, 6, 8, 17 |
| L3 | Connection geometry, operator necessity, dual-loop | 2-4, 10, 13, 16, 23-26, 33-35, 37-38 |
| L4 | Chirality, sequence ordering, type weighting | 2-3, 17, 25-26, 28, 32, 35-36 |
| L5 | Torus topology, loop laws, compound legos | 8, 11, 14-15, 17, 29-32 |
| L6 | Axis polarity, master engine | 27, 36, 38 |
| L7 | Axis 0, full engine integration | 16-17, 27 |

---

*This index is authoritative for battery enumeration. If a new battery is added to `system_v4/probes/`, it must be registered here.*
