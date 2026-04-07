# Migration Registry — Irreducible Family PyTorch Migration

## Document Status

| Field | Value |
|-------|-------|
| **last_verified** | 2026-04-07 |
| **status** | Machine-generated from repo scan. Cross-referenced against PYTORCH_RATCHET_BUILD_PLAN.md and actual probe files in `system_v4/probes/`. |
| **authority** | This is the authoritative family-level migration registry. ENFORCEMENT_AND_PROCESS_RULES.md defers here for migration state. |
| **source_of_truth** | PYTORCH_RATCHET_BUILD_PLAN.md defines the 28 irreducible families. This doc tracks their actual migration state against the filesystem. |

---

## Registry

| # | Family | Baseline sim file | Baseline sim exists? | Torch module | Tools needed | Negative battery | Negative battery exists? | Promotion status | Notes |
|---|--------|-------------------|----------------------|--------------|--------------|------------------|--------------------------|------------------|-------|
| 1 | density_matrix | sim_pure_lego_density_matrices.py | YES | torch DensityMatrix | sympy, z3 | sim_negative_density_matrices.py | YES | NOT_STARTED | — |
| 2 | purification | sim_pure_lego_density_matrices.py | YES | torch Purification | sympy, z3 | sim_negative_density_matrices.py | YES | NOT_STARTED | Shares baseline with density_matrix |
| 3 | z_dephasing | sim_pure_lego_channels.py | **NO** | torch ZDephasing | z3, clifford | sim_negative_channels.py | YES | NOT_STARTED | Build plan references nonexistent file. Nearest actual: `sim_pure_lego_channels_choi_lindblad.py` |
| 4 | x_dephasing | sim_pure_lego_channels.py | **NO** | torch XDephasing | z3, clifford | sim_negative_channels.py | YES | NOT_STARTED | Same missing baseline as #3 |
| 5 | depolarizing | sim_pure_lego_channels.py | **NO** | torch Depolarizing | z3 | sim_negative_channels.py | YES | NOT_STARTED | Same missing baseline as #3 |
| 6 | amplitude_damping | sim_pure_lego_channels.py | **NO** | torch AmplitudeDamping | z3, sympy | sim_negative_channels.py | YES | NOT_STARTED | Same missing baseline as #3 |
| 7 | phase_damping | sim_pure_lego_channels.py | **NO** | torch PhaseDamping | z3 | sim_negative_channels.py | YES | NOT_STARTED | Same missing baseline as #3 |
| 8 | bit_flip | sim_pure_lego_channels.py | **NO** | torch BitFlip | z3 | sim_negative_channels.py | YES | NOT_STARTED | Same missing baseline as #3 |
| 9 | phase_flip | sim_pure_lego_channels.py | **NO** | torch PhaseFlip | z3 | sim_negative_channels.py | YES | NOT_STARTED | Same missing baseline as #3 |
| 10 | bit_phase_flip | sim_pure_lego_channels.py | **NO** | torch BitPhaseFlip | z3 | sim_negative_channels.py | YES | NOT_STARTED | Same missing baseline as #3 |
| 11 | unitary_rotation | sim_pure_lego_channels.py | **NO** | torch UnitaryRotation | clifford, sympy | sim_negative_channels.py | YES | NOT_STARTED | Same missing baseline as #3 |
| 12 | z_measurement | sim_pure_lego_channels.py | **NO** | torch ZMeasurement | z3 | sim_negative_channels.py | YES | NOT_STARTED | Same missing baseline as #3 |
| 13 | CNOT | sim_pure_lego_entanglement.py | **NO** | torch CNOT | z3, sympy | sim_negative_entanglement.py | YES | NOT_STARTED | Build plan references nonexistent file. Nearest actual: `sim_pure_lego_gates_decompositions.py`, `sim_pure_lego_ent_swapping_distillation.py` |
| 14 | CZ | sim_pure_lego_entanglement.py | **NO** | torch CZ | z3 | sim_negative_entanglement.py | YES | NOT_STARTED | Same missing baseline as #13 |
| 15 | SWAP | sim_pure_lego_entanglement.py | **NO** | torch SWAP | z3 | sim_negative_entanglement.py | YES | NOT_STARTED | Same missing baseline as #13 |
| 16 | Hadamard | sim_pure_lego_channels.py | **NO** | torch Hadamard | z3, clifford | sim_negative_channels.py | YES | NOT_STARTED | Same missing baseline as #3 |
| 17 | T_gate | sim_pure_lego_channels.py | **NO** | torch TGate | z3 | sim_negative_channels.py | YES | NOT_STARTED | Same missing baseline as #3 |
| 18 | iSWAP | sim_pure_lego_entanglement.py | **NO** | torch iSWAP | z3 | sim_negative_entanglement.py | YES | NOT_STARTED | Same missing baseline as #13 |
| 19 | cartan_kak | sim_pure_lego_entanglement.py | **NO** | torch CartanKAK | sympy, clifford | sim_negative_entanglement.py | YES | NOT_STARTED | Same missing baseline as #13. No dedicated cartan baseline file exists. |
| 20 | eigenvalue_decomposition | sim_pure_lego_density_matrices.py | YES | torch EigenDecomp | sympy | sim_negative_density_matrices.py | YES | NOT_STARTED | — |
| 21 | husimi_q | sim_pure_lego_density_matrices.py | YES | torch HusimiQ | sympy | sim_negative_density_matrices.py | YES | NOT_STARTED | No dedicated husimi baseline; covered inside density_matrices |
| 22 | l1_coherence | sim_pure_lego_coherence.py | **NO** | torch L1Coherence | z3, sympy | sim_negative_entropy_boundaries.py | YES | NOT_STARTED | Build plan references nonexistent file. Nearest actual: `sim_pure_lego_majorization_steering_coherence.py` |
| 23 | relative_entropy_coherence | sim_pure_lego_coherence.py | **NO** | torch RECoherence | z3, sympy | sim_negative_entropy_boundaries.py | YES | NOT_STARTED | Same missing baseline as #22 |
| 24 | wigner_negativity | sim_pure_lego_density_matrices.py | YES | torch WignerNegativity | sympy | sim_negative_density_matrices.py | YES | NOT_STARTED | Dedicated file also exists: `sim_pure_lego_wigner_quasiprobability.py` |
| 25 | hopf_connection | sim_pure_lego_geometry.py | **NO** | torch HopfConnection | clifford, toponetx | sim_negative_geometry.py | YES | NOT_STARTED | Build plan references nonexistent file. Nearest actual: `sim_pure_lego_symplectic_kahler_weyl.py` (Weyl/geometry content). No dedicated Hopf baseline exists. |
| 26 | chiral_overlap | sim_pure_lego_geometry.py | **NO** | torch ChiralOverlap | clifford | sim_negative_geometry.py | YES | NOT_STARTED | Same missing baseline as #25. No dedicated chiral baseline exists. |
| 27 | mutual_information | sim_pure_lego_entropy.py | **NO** | torch MutualInformation | z3, sympy | sim_negative_entropy_boundaries.py | YES | NOT_STARTED | Build plan references nonexistent file. Nearest actual: `sim_pure_lego_quantum_shannon.py`, `sim_pure_lego_f_divergences.py` |
| 28 | quantum_discord | sim_pure_lego_entropy.py | **NO** | torch QuantumDiscord | z3, sympy | sim_negative_entropy_boundaries.py | YES | NOT_STARTED | Same missing baseline as #27. Also: `sim_pure_lego_all_axes_discord.py` exists (discord-specific). |

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
| Baseline file EXISTS | 7 | #1 density_matrix, #2 purification, #20 eigenvalue_decomposition, #21 husimi_q, #24 wigner_negativity (all via `sim_pure_lego_density_matrices.py`) |
| Baseline file MISSING | 21 | #3-12 (channels), #13-15,18-19 (entanglement/gates), #16-17 (gates via channels), #22-23 (coherence), #25-26 (geometry), #27-28 (entropy) |

**The build plan references 6 baseline filenames that do not exist in the repo:**

| Referenced filename | Exists? | Nearest actual file(s) |
|---------------------|---------|------------------------|
| `sim_pure_lego_channels.py` | NO | `sim_pure_lego_channels_choi_lindblad.py`, `sim_pure_lego_channel_capacity.py` |
| `sim_pure_lego_entanglement.py` | NO | `sim_pure_lego_ent_swapping_distillation.py`, `sim_pure_lego_gates_decompositions.py` |
| `sim_pure_lego_coherence.py` | NO | `sim_pure_lego_majorization_steering_coherence.py` |
| `sim_pure_lego_geometry.py` | NO | `sim_pure_lego_symplectic_kahler_weyl.py` |
| `sim_pure_lego_entropy.py` | NO | `sim_pure_lego_quantum_shannon.py`, `sim_pure_lego_f_divergences.py`, `sim_pure_lego_all_axes_discord.py` |
| `sim_pure_lego_density_matrices.py` | YES | — |

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

1. **21 of 28 families have no matching baseline file** at the path listed in PYTORCH_RATCHET_BUILD_PLAN.md. Either the build plan filenames need correction to point to actual files, or new dedicated baseline sims need to be written for those families.
2. **Zero torch modules exist.** Phase 3 has not begun.
3. **No family has progressed beyond NOT_STARTED.** The entire migration is pre-Phase-3.
