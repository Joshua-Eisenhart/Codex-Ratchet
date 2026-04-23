# Terrain Law Ledger

**Date:** 2026-03-29
**Status:** LOCKED — derived from probe-validated axis math (AXIS_3_4_5_6_QIT_MATH.md + sim_64_address_audit.py)
**Sources:** sim_Ax3_density_path.py ✓, sim_Ax5_TF_kernel.py ✓, sim_64_address_audit.py ✓

---

## 1. Axis Encoding Key

| Axis | Value | Meaning |
|---|---|---|
| **Ax0** (b₀) | +1 | N-type: upper hemisphere, η < π/4, sgn(r_z) > 0 |
| **Ax0** (b₀) | -1 | S-type: lower hemisphere, η > π/4, sgn(r_z) < 0 |
| **Ax1** (b₁) | U | Isothermal (Se, Ni): dissipative Lindblad generator |
| **Ax1** (b₁) | NU | Adiabatic (Ne, Si): unitary Hamiltonian generator |
| **Ax2** (b₂) | D | Direct (Se, Ne): lab frame, V_s(u) = I |
| **Ax2** (b₂) | C | Conjugated (Ni, Si): co-rotating Weyl frame, V_s(u) ≠ I |
| **Ax3** (b₃) | -1 | Inner/fiber: density-stationary path, d(ρ)/du = 0 |
| **Ax3** (b₃) | +1 | Outer/base: density-traversing path, d(ρ)/du ≠ 0 |
| **Ax5-i** | Ti, Fi | "i-operators" native to direct terrains (Se, Ne, Ax2=D) |
| **Ax5-e** | Te, Fe | "e-operators" native to conjugated terrains (Ni, Si, Ax2=C) |
| **Ax6** (b₆) | UP | Op-first token order: [Op][Terrain] e.g. TiNe |
| **Ax6** (b₆) | DOWN | Terrain-first token order: [Terrain][Op] e.g. NeTi |

**Derivation:** b₆ = −b₀ × b₃ (proven: 0 violations in 64-address audit)

---

## 2. Eight-Terrain Axis Annotation Table

| Stage | Terrain | b₀ | Ax1 | b₂ | b₃ | Native ops | b₆ | Token order |
|---|---|---|---|---|---|---|---|---|
| Se_f | Se fiber | -1 (S) | U | D | -1 (inner) | Ti, Fi | -1 → DOWN | SeTi, SeFi |
| Si_f | Si fiber | -1 (S) | NU | C | -1 (inner) | Te, Fe | -1 → DOWN | SiTe, SiFe |
| Ne_f | Ne fiber | +1 (N) | NU | D | -1 (inner) | Ti, Fi | +1 → UP | TiNe, FiNe |
| Ni_f | Ni fiber | +1 (N) | U | C | -1 (inner) | Te, Fe | +1 → UP | TeNi, FeNi |
| Se_b | Se base | -1 (S) | U | D | +1 (outer) | Ti, Fi | +1 → UP | TiSe, FiSe |
| Si_b | Si base | -1 (S) | NU | C | +1 (outer) | Te, Fe | +1 → UP | TeSi, FeSi |
| Ne_b | Ne base | +1 (N) | NU | D | +1 (outer) | Ti, Fi | -1 → DOWN | NeTi, NeFi |
| Ni_b | Ni base | +1 (N) | U | C | +1 (outer) | Te, Fe | -1 → DOWN | NiTe, NiFe |

**Ax6 derivation check:**
- Se_f: b₆ = −(−1)(−1) = −1 ✓
- Ne_b: b₆ = −(+1)(+1) = −1 ✓
- Ni_f: b₆ = −(+1)(−1) = +1 ✓
- Si_b: b₆ = −(−1)(+1) = +1 ✓

---

## 3. Operator Lattice — Laws per Terrain

Each terrain receives all 4 operators (Ti, Fe, Te, Fi) in every subcycle.
The laws below describe the QIT effect for each operator on each terrain.
"Native" = operator class matches terrain Ax5 affinity. "Visiting" = cross-affinity.

### Se_f (Se fiber — S / U / Direct / Inner / DOWN)
**Native ops:** Ti (σ_z dephasing), Fi (U_x rotation) | Visiting: Te, Fe

| Op | Status | QIT Law |
|---|---|---|
| **Ti** | NATIVE | σ_z dephasing reinforces Se dissipative structure; clamps fiber phase. Entropy ↑. |
| **Fi** | NATIVE | U_x rotation on Se fiber; injects coherent circulation into the dissipative funnel. Negentropy pulse. |
| **Te** | VISITING | σ_x dephasing (conjugated-frame op) on direct terrain; cross-axis disruption of Se Lindblad generator. |
| **Fe** | VISITING | U_z rotation (conjugated-frame op) on direct terrain; adds z-phase on top of dissipative flow. |

Token order: DOWN → SeTi, SeFi (native); SeTe, SeFe (visiting)

### Si_f (Si fiber — S / NU / Conjugated / Inner / DOWN)
**Native ops:** Te (σ_x dephasing), Fe (U_z rotation) | Visiting: Ti, Fi

| Op | Status | QIT Law |
|---|---|---|
| **Te** | NATIVE | σ_x dephasing in conjugated Si frame; disrupts Si invariant strata. Entropy ↑ (transient). |
| **Fe** | NATIVE | U_z rotation in Si Hamiltonian flow; advances phase within invariant strata. Purity-preserving. |
| **Ti** | VISITING | σ_z dephasing (direct-frame op) on conjugated terrain; temporarily breaks adiabatic invariance. |
| **Fi** | VISITING | U_x rotation (direct-frame op); selects among Si strata via cross-frame filter. |

Token order: DOWN → SiTe, SiFe (native); SiTi, SiFi (visiting)

### Ne_f (Ne fiber — N / NU / Direct / Inner / UP)
**Native ops:** Ti (σ_z dephasing), Fi (U_x rotation) | Visiting: Te, Fe

| Op | Status | QIT Law |
|---|---|---|
| **Ti** | NATIVE | σ_z dephasing breaks Ne phase circulation; clamps the spiraling vortex. Entropy ↑. |
| **Fi** | NATIVE | U_x rotation selects among Ne circulation modes. Purity ≈ preserved. |
| **Te** | VISITING | σ_x dephasing (conjugated-frame op) on Ne vortex; explores off-axis Ne modes. |
| **Fe** | VISITING | U_z rotation adds co-phasing to Ne circulation; can amplify or cancel vortex mode. |

Token order: UP → TiNe, FiNe (native); TeNe, FeNe (visiting)

### Ni_f (Ni fiber — N / U / Conjugated / Inner / UP)
**Native ops:** Te (σ_x dephasing), Fe (U_z rotation) | Visiting: Ti, Fi

| Op | Status | QIT Law |
|---|---|---|
| **Te** | NATIVE | σ_x dephasing in conjugated Ni frame; dissipates Ni coherence in the rotating frame. |
| **Fe** | NATIVE | U_z rotation in conjugated Ni frame; steers the attractor phase without disrupting collapse. |
| **Ti** | VISITING | σ_z dephasing (direct-frame op) on Ni; partially decoheres the collapse trajectory cross-frame. |
| **Fi** | VISITING | U_x rotation (direct-frame op); injects direct-frame unitary into conjugated attractor basin. |

Token order: UP → TeNi, FeNi (native); TiNi, FiNi (visiting)

### Se_b (Se base — S / U / Direct / Outer / UP)
**Native ops:** Ti (σ_z dephasing), Fi (U_x rotation) | Visiting: Te, Fe

| Op | Status | QIT Law |
|---|---|---|
| **Ti** | NATIVE | σ_z dephasing on Se base-lift; constrains torus transport, clamps density traversal. Entropy ↑. |
| **Fi** | NATIVE | U_x rotation on Se outer loop; coherent kick into the dissipative base-lift flow. |
| **Te** | VISITING | σ_x dephasing (conjugated-frame op) on Se outer; cross-axis exploration of base manifold. |
| **Fe** | VISITING | U_z rotation (conjugated-frame op) on Se base; imparts conjugated-frame phase on dissipative terrain. |

Token order: UP → TiSe, FiSe (native); TeSe, FeSe (visiting)

### Si_b (Si base — S / NU / Conjugated / Outer / UP)
**Native ops:** Te (σ_x dephasing), Fe (U_z rotation) | Visiting: Ti, Fi

| Op | Status | QIT Law |
|---|---|---|
| **Te** | NATIVE | σ_x dephasing on Si base-lift in conjugated frame; disrupts adiabatic strata traversal. |
| **Fe** | NATIVE | U_z rotation on Si outer loop; advances strata traversal coherently. Purity-preserving. |
| **Ti** | VISITING | σ_z dephasing (direct-frame op) on Si outer; transient entropy spike on adiabatic terrain. |
| **Fi** | VISITING | U_x rotation (direct-frame op) selects among Si strata on outer path. |

Token order: UP → TeSi, FeSi (native); TiSi, FiSi (visiting)

### Ne_b (Ne base — N / NU / Direct / Outer / DOWN)
**Native ops:** Ti (σ_z dephasing), Fi (U_x rotation) | Visiting: Te, Fe

| Op | Status | QIT Law |
|---|---|---|
| **Ti** | NATIVE | σ_z dephasing breaks Ne outer vortex; collapses base-lift circulation into mixed state. Entropy ↑. |
| **Fi** | NATIVE | U_x rotation selects among Ne outer circulation modes. Purity ≈ preserved. |
| **Te** | VISITING | σ_x dephasing on Ne outer (conjugated-frame op); cross-axis exploration of Ne base geometry. |
| **Fe** | VISITING | U_z rotation on Ne base-lift; amplifies or redirects vortex mode in conjugated frame. |

Token order: DOWN → NeTi, NeFi (native); NeTe, NeFe (visiting)

### Ni_b (Ni base — N / U / Conjugated / Outer / DOWN)
**Native ops:** Te (σ_x dephasing), Fe (U_z rotation) | Visiting: Ti, Fi

| Op | Status | QIT Law |
|---|---|---|
| **Te** | NATIVE | σ_x dephasing on Ni outer; dissipates attractor coherence during base traversal. |
| **Fe** | NATIVE | U_z rotation on Ni outer loop in conjugated frame; steers attractor approach on base-lift path. |
| **Ti** | VISITING | σ_z dephasing (direct-frame op) on Ni outer; cross-frame disruption of attractor base traversal. |
| **Fi** | VISITING | U_x rotation (direct-frame op) selects among Ni attractor modes during base traversal. |

Token order: DOWN → NiTe, NiFe (native); NiTi, NiFi (visiting)

---

## 4. Derivation Notes

### Ax5 Native vs Visiting Rule

The affinity rule assigns operators to terrains by frame class (Ax2), using the **i/e operator split** (not T/F class split):

- **i-operators** (Ti, Fi): native to direct-frame terrains (Se, Ne, Ax2=D)
- **e-operators** (Te, Fe): native to conjugated-frame terrains (Ni, Si, Ax2=C)

This is because:
- Ti and Fi have subscript "i" → interact with the identity-frame (direct/lab) structure
- Te and Fe have subscript "e" → interact with the external/conjugated-frame structure

Both T-class (dephasing) and F-class (rotation) operators appear natively on each terrain type:
- Direct terrains host one T-native (Ti) and one F-native (Fi)
- Conjugated terrains host one T-native (Te) and one F-native (Fe)

Source: AXIS_3_4_5_6_QIT_MATH.md — "Ti, Fi pair with direct terrains (Se, Ne, Ax2=direct); Te, Fe pair with conjugated terrains (Ni, Si, Ax2=conjugated)."
Verified: sim_64_address_audit.py C3 check (0 violations across 64 entries).

"Native" = operator's frame matches terrain's Ax2 frame. "Visiting" operators still execute every subcycle but induce cross-frame effects.

### Ax4 Derivation from Ax3 × Engine

Ax4 is derived, not primitive. The loop ordering (UEUE vs EUEU) follows from:
- **Ax3 inner (fiber)**: Density-stationary path → U-first ordering (Deductive, FeTi)
- **Ax3 outer (base)**: Density-traversing path → E-first ordering (Inductive, TeFi)

Where U = Ne/Si class (NU/unitary branch) and E = Se/Ni class (U/dissipative branch).

### Ax6 Proof-of-Validity

The b₆ = −b₀ × b₃ rule is verified across all 64 microsteps in `sim_64_address_audit.py` (0 violations). The derivation follows from the structural closure of the Ax0 × Ax3 intersection:
- b₀ encodes hemisphere (N/S orientation)
- b₃ encodes loop class (fiber/base)
- Their product determines token-order precedence (which axis "leads")

---

## 5. Cross-Reference

| Topic | Source |
|---|---|
| Axis definitions | AXIS_3_4_5_6_QIT_MATH.md |
| Operator math | v5_OPERATOR_MATH_LEDGER.md (via sim_Ax5_TF_kernel.py) |
| Terrain geometry | TERRAIN_NAMING_MATH_LEDGER.md |
| 64-address uniqueness | sim_64_address_audit.py (PASS ✓) |
| Fiber/base loop probe | sim_Ax3_density_path.py (PASS ✓) |
| T/F kernel probe | sim_Ax5_TF_kernel.py (PASS ✓) |
| Runtime operators | geometric_operators.py (corrected 2026-03-29) |
