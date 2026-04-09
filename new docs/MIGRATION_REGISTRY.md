# Migration Registry — Irreducible Family PyTorch Migration

## Document Status

| Field | Value |
|-------|-------|
| **last_verified** | 2026-04-08 |
| **status** | Verified 2026-04-08: NOT_STARTED is correct — no standalone torch module files exist yet. Numpy baselines exist for most families (Baseline sim exists? column is accurate). The PYTORCH_RATCHET_BUILD_PLAN.md Phase 7 "PASS" entries refer to C1/C3/C4 criteria only; C2_graph_topology: 11/28 non-null, 0 mismatches (per 2026-04-09 audit). |
| **authority** | This is the authoritative family-level migration registry. ENFORCEMENT_AND_PROCESS_RULES.md defers here for migration state. |
| **source_of_truth** | PYTORCH_RATCHET_BUILD_PLAN.md defines the 28 irreducible families. This doc tracks their actual migration state against the filesystem. |

---

## Registry

| # | Family | Baseline sim file | Baseline sim exists? | Torch module | Tools needed | Negative battery | Negative battery exists? | Promotion status | Notes |
|---|--------|-------------------|----------------------|--------------|--------------|------------------|--------------------------|------------------|-------|
| 1 | density_matrix | sim_pure_lego_density_matrices.py | YES | torch DensityMatrix | sympy, z3 | sim_negative_density_matrices.py | YES | NOT_STARTED | `build_states()`, `is_valid_dm()`, `pauli_decompose()`, `pauli_reconstruct()` |
| 2 | purification | sim_pure_lego_density_matrices.py | **PARTIAL** | torch Purification | sympy, z3 | sim_negative_density_matrices.py | YES | NOT_STARTED | No standalone purification function. Purification is used implicitly in `sim_pure_lego_quantum_shannon.py` (coherent info via purification) and `sim_pure_lego_ent_swapping_distillation.py` (distillation). No dedicated `purify(rho)` exists. |
| 3 | z_dephasing | sim_pure_lego_channels_choi_lindblad.py | YES | torch ZDephasing | z3, clifford | sim_negative_channels.py | YES | NOT_STARTED | `z_dephasing(rho, s=0.3)` at line 165 |
| 4 | x_dephasing | sim_pure_lego_channels_choi_lindblad.py | YES | torch XDephasing | z3, clifford | sim_negative_channels.py | YES | NOT_STARTED | `x_dephasing(rho, s=0.3)` at line 171 |
| 5 | depolarizing | sim_pure_lego_channels_choi_lindblad.py | YES | torch Depolarizing | z3 | sim_negative_channels.py | YES | NOT_STARTED | `depolarizing(rho, p=0.3)` at line 147 |
| 6 | amplitude_damping | sim_pure_lego_channels_choi_lindblad.py | YES | torch AmplitudeDamping | z3, sympy | sim_negative_channels.py | YES | NOT_STARTED | `amplitude_damping(rho, g=0.3)` at line 153 |
| 7 | phase_damping | sim_pure_lego_channels_choi_lindblad.py | YES | torch PhaseDamping | z3 | sim_negative_channels.py | YES | NOT_STARTED | `phase_damping(rho, l=0.3)` at line 159 |
| 8 | bit_flip | sim_pure_lego_channels_choi_lindblad.py | YES | torch BitFlip | z3 | sim_negative_channels.py | YES | NOT_STARTED | `bit_flip(rho, p=0.3)` at line 135 |
| 9 | phase_flip | sim_pure_lego_channels_choi_lindblad.py | YES | torch PhaseFlip | z3 | sim_negative_channels.py | YES | NOT_STARTED | `phase_flip(rho, p=0.3)` at line 139 |
| 10 | bit_phase_flip | sim_pure_lego_channels_choi_lindblad.py | YES | torch BitPhaseFlip | z3 | sim_negative_channels.py | YES | NOT_STARTED | `bit_phase_flip(rho, p=0.3)` at line 143 |
| 11 | unitary_rotation | sim_pure_lego_channels_choi_lindblad.py | **PARTIAL** | torch UnitaryRotation | clifford, sympy | sim_negative_channels.py | YES | NOT_STARTED | No standalone `unitary_rotation()` in channels file. Choi/Kraus/Lindblad infrastructure exists. Incidental usage in `sim_pure_lego_mega_protocols.py` line 402. Needs dedicated baseline. |
| 12 | z_measurement | **NONE** | **NO** | torch ZMeasurement | z3 | sim_negative_channels.py | YES | NOT_STARTED | No dedicated z_measurement function in any sim_pure_lego file. Measurement functions exist in other files (`cloning_qkd_illumination`, `tomography_shadow`, `qec`, `state_discrimination`) but none are z-measurement-specific legos. **Needs new baseline.** |
| 13 | CNOT | sim_pure_lego_gates_decompositions.py | YES | torch CNOT | z3, sympy | sim_negative_entanglement.py | YES | NOT_STARTED | `cnot()` at line 99 |
| 14 | CZ | sim_pure_lego_gates_decompositions.py | YES | torch CZ | z3 | sim_negative_entanglement.py | YES | NOT_STARTED | `cz()` at line 116 |
| 15 | SWAP | sim_pure_lego_gates_decompositions.py | YES | torch SWAP | z3 | sim_negative_entanglement.py | YES | NOT_STARTED | `swap_gate()` at line 578 |
| 16 | Hadamard | sim_pure_lego_stabilizer_magic.py | YES | torch Hadamard | z3, clifford | sim_negative_channels.py | YES | NOT_STARTED | `H_gate` constant at line 37; used throughout Clifford group generation |
| 17 | T_gate | sim_pure_lego_stabilizer_magic.py | YES | torch TGate | z3 | sim_negative_channels.py | YES | NOT_STARTED | `T_gate` constant at line 368; non-Clifford verification at line 390-392 |
| 18 | iSWAP | sim_pure_lego_gates_decompositions.py | YES | torch iSWAP | z3 | sim_negative_entanglement.py | YES | NOT_STARTED | `iswap()` at line 570 |
| 19 | cartan_kak | sim_pure_lego_gates_decompositions.py | YES | torch CartanKAK | sympy, clifford | sim_negative_entanglement.py | YES | NOT_STARTED | `cartan_decompose(U)` at line 497. Also Weyl coordinates in `sim_pure_lego_symplectic_kahler_weyl.py` line 418. |
| 20 | eigenvalue_decomposition | sim_pure_lego_density_matrices.py | YES | torch EigenDecomp | sympy | sim_negative_density_matrices.py | YES | NOT_STARTED | Spectral decomposition section (line 204 results key). `np.linalg.eigh` used throughout. |
| 21 | husimi_q | sim_pure_lego_wigner_quasiprobability.py | YES | torch HusimiQ | sympy | sim_negative_density_matrices.py | YES | NOT_STARTED | `husimi_q_grid(rho)` at line 208, `husimi_stats(rho)` at line 223 |
| 22 | l1_coherence | sim_pure_lego_majorization_steering_coherence.py | YES | torch L1Coherence | z3, sympy | sim_negative_entropy_boundaries.py | YES | NOT_STARTED | `l1_coherence(rho)` at line 574 |
| 23 | relative_entropy_coherence | sim_pure_lego_majorization_steering_coherence.py | YES | torch RECoherence | z3, sympy | sim_negative_entropy_boundaries.py | YES | NOT_STARTED | `relative_entropy_coherence(rho)` at line 578 |
| 24 | wigner_negativity | sim_pure_lego_wigner_quasiprobability.py | YES | torch WignerNegativity | sympy | sim_negative_density_matrices.py | YES | NOT_STARTED | `wigner_negativity(W)` at line 145, `discrete_wigner_d2()` at line 106 |
| 25 | hopf_connection | sim_pure_lego_quaternion_octonion.py | YES | torch HopfConnection | clifford, toponetx | sim_negative_geometry.py | YES | NOT_STARTED | `test_hopf_fibrations()` at line 583; `hopf_C`, `hopf_H`, `hopf_O` at lines 606/642/680. Also: `sim_pure_lego_topology_graphs.py` has torus cell complex. |
| 26 | chiral_overlap | **NONE** | **NO** | torch ChiralOverlap | clifford | sim_negative_geometry.py | YES | NOT_STARTED | No chiral_overlap function exists in any sim_pure_lego file. No Weyl spinor chirality/handedness implementation found. **Needs new baseline.** |
| 27 | mutual_information | sim_pure_lego_all_axes_discord.py | YES | torch MutualInformation | z3, sympy | sim_negative_entropy_boundaries.py | YES | NOT_STARTED | `mutual_information(rho_AB)` at line 414 |
| 28 | quantum_discord | sim_pure_lego_all_axes_discord.py | YES | torch QuantumDiscord | z3, sympy | sim_negative_entropy_boundaries.py | YES | NOT_STARTED | `quantum_discord(rho_AB, n_theta, n_phi)` at line 420 |

---

## Promotion Status Definitions

| Status | Meaning |
|--------|---------|
| **NOT_STARTED** | No torch module exists. May or may not have a numpy baseline. |
| **BASELINE_ONLY** | Numpy baseline sim exists and passes. No torch code written. |
| **TORCH_DRAFT** | Torch module written but not yet tested against baseline or negative battery. |
| **TORCH_TESTED** | Torch module tested against baseline (numerical match) AND negative battery (failures confirmed). |
| **CANONICAL** | Torch module passes all tests, integrated into constraint graph, ready for Phase 4+. |

---

## Summary

### Promotion status counts

| Status | Count |
|--------|-------|
| NOT_STARTED | 28 |
| BASELINE_ONLY | 0 |
| TORCH_DRAFT | 0 |
| TORCH_TESTED | 0 |
| CANONICAL | 0 |

**Total families: 28. Zero torch modules exist.**

### Baseline sim file status

| Status | Count | Families |
|--------|-------|----------|
| Baseline file EXISTS (full impl) | 24 | #1 density_matrix, #3-10 channels, #13-15 CNOT/CZ/SWAP, #16-17 Hadamard/T_gate, #18 iSWAP, #19 cartan_kak, #20 eigenvalue_decomposition, #21 husimi_q, #22-23 coherence, #24 wigner_negativity, #25 hopf_connection, #27-28 mutual_info/discord |
| Baseline file PARTIAL (impl exists but not standalone) | 2 | #2 purification, #11 unitary_rotation |
| Baseline file MISSING (no impl found) | 2 | #12 z_measurement, #26 chiral_overlap |

### Corrected file mapping (was 5 ghost filenames, now resolved)

| Old ghost filename | Actual file(s) | Families served |
|--------------------|----------------|-----------------|
| `sim_pure_lego_channels.py` | `sim_pure_lego_channels_choi_lindblad.py` | #3-11 (channels) |
| `sim_pure_lego_entanglement.py` | `sim_pure_lego_gates_decompositions.py` | #13-15, #18-19 (gates) |
| `sim_pure_lego_coherence.py` | `sim_pure_lego_majorization_steering_coherence.py` | #22-23 (coherence) |
| `sim_pure_lego_geometry.py` | `sim_pure_lego_quaternion_octonion.py` (Hopf), **NONE** (chiral) | #25 hopf, #26 chiral |
| `sim_pure_lego_entropy.py` | `sim_pure_lego_all_axes_discord.py` | #27-28 (entropy/discord) |

### Additional files discovered with relevant content

| File | Relevant families |
|------|-------------------|
| `sim_pure_lego_stabilizer_magic.py` | #16 Hadamard (H_gate), #17 T_gate |
| `sim_pure_lego_wigner_quasiprobability.py` | #21 husimi_q, #24 wigner_negativity |
| `sim_pure_lego_symplectic_kahler_weyl.py` | #19 cartan_kak (Weyl coordinates), #25 hopf (symplectic/Kahler geometry) |
| `sim_pure_lego_quantum_shannon.py` | #2 purification (implicit via coherent info) |
| `sim_pure_lego_mega_protocols.py` | #11 unitary_rotation (incidental, line 402) |

### Negative battery status

| Battery file | Exists? | Covers families |
|--------------|---------|-----------------|
| `sim_negative_density_matrices.py` | YES | #1, 2, 20, 21, 24 |
| `sim_negative_channels.py` | YES | #3-12, 16, 17 |
| `sim_negative_entanglement.py` | YES | #13-15, 18, 19 |
| `sim_negative_entropy_boundaries.py` | YES | #22, 23, 27, 28 |
| `sim_negative_geometry.py` | YES | #25, 26 |

**All 5 referenced negative battery files exist. Zero missing.**

### Critical gaps requiring action

1. **2 of 28 families have NO baseline implementation:** #12 z_measurement, #26 chiral_overlap. These need new baseline sims written.
2. **2 of 28 families have PARTIAL baselines:** #2 purification (no standalone `purify(rho)` function), #11 unitary_rotation (no standalone rotation-as-channel function). These may need dedicated baseline functions extracted or written.
3. **Zero torch modules exist.** Phase 3 has not begun.
4. **No family has progressed beyond NOT_STARTED.** The entire migration is pre-Phase-3.
