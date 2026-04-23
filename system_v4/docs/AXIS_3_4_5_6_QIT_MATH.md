# Axis 3–4–5–6 QIT Math Packet

**Date:** 2026-03-29
**Epistemic status:** 
- Ax2 is now locked to the **Weyl Interaction Picture** (interaction frame rotation).
- Ax0 continuous field is seated in the **Torus Latitude η** (entropy gradient).
- Ax0 discrete bit is locked to the **Hemisphere Threshold** (sgn(r_z)).
- Ax6 is proven to be **Derived** from Ax0 × Ax3.

---

## Axis 0: Torus Entropy & Hemisphere Threshold

**Source:** `torus latitude entropy audit`

The torus latitude $\eta$ is the fundamental entropy coordinate on $M(C)$. 

### Continuous Field: $\varphi_0 \sim S(\bar{\rho}(\eta))$

A pure spinor averaged over its torus longitude $\chi$ becomes a mixed state:
$$ \bar{\rho}(\eta) = \frac{1}{2\pi} \int_0^{2\pi} \rho(\chi, \eta) d\chi = \text{diag}(\cos^2\eta, \sin^2\eta) $$

The entropy of this orbit-family is:
$$ S(\bar{\rho}(\eta)) = -\cos^2\eta \ln\cos^2\eta - \sin^2\eta \ln\sin^2\eta $$

| Latitude η | Entropy $S$ | Geometry | Role |
|---|---|---|---|
| $0$ | $0$ | North Pole ($|0\rangle$) | Pure State |
| $\pi/4$ | $\ln 2$ | Clifford Torus | Max Entropy |
| $\pi/2$ | $0$ | South Pole ($|1\rangle$) | Pure State |

### Discrete Binarization: $b_0 = \text{sgn}(\cos(2\eta)) = \text{sgn}(r_z)$

| Region | Latitude η | $r_z$ | Label | $b_0$ |
|---|---|---|---|---|
| Upper | $\eta < \pi/4$ | $> 0$ | N / White | $+1$ |
| Threshold | $\eta = \pi/4$ | $0$ | Clifford | $0$ |
| Lower | $\eta > \pi/4$ | $< 0$ | S / Black | $-1$ |

---

## Axis 2: The Weyl Interaction Picture

**Source:** `interaction picture lock`

The frame unitary $V(u)$ for Ax2 is identified as the **Weyl sheet free evolution**:
$$ V_s(u) = e^{-i H_s u}, \quad H_s = \pm H_0 $$

This defines the **Interaction Picture** for each sheet:
- **Ax2 Conjugated (Ni, Si)**: Dynamics seen from the co-rotating Weyl frame ($V_s(u) \neq I$). The $K$ term is the sheet Hamiltonian $H_s$.
- **Ax2 Direct (Se, Ne)**: Dynamics in the fixed lab frame ($V_s(u) = I$).

| Sheet | $V_s(u)$ | $K_s$ | Rep Frame |
|---|---|---|---|
| **Left** | $e^{-i(+H_0)u}$ | $+H_0$ | Conjugated (for Ni/Si) |
| **Right** | $e^{-i(-H_0)u}$ | $-H_0$ | Conjugated (for Ni/Si) |

---

## Axis 6: Precedence (Derived XOR)

**Source:** `structural algebraic closure`

Axis 6 is NOT a primitive degree of freedom. It is the derived composition order resulting from the intersection of topology (Ax0) and loop-type (Ax3).

### The Derived Rule: $b_6 = -b_0 b_3$

| Loop Type ($b_3$) | Color ($b_0$) | Pred ($b_6$) | Label |
|---|---|---|---|
| inner (-1) | white (+1) | $+1$ | **UP** (Op-first) |
| inner (-1) | black (-1) | $-1$ | **DOWN** (Terrain-first) |
| outer (+1) | white (+1) | $-1$ | **DOWN** (Terrain-first) |
| outer (+1) | black (-1) | $+1$ | **UP** (Op-first) |

**Verification**: This rule matches all 16 stage-token assignments. 
- `inner + N` → `UP` (e.g., `TiNe`)
- `outer + N` → `DOWN` (e.g., `NeTi`)

---

## Axis 4: Deductive vs Inductive Kernels

The two loop orientations are distinguished by the non-commutativity of the CPTP semigroup:

- **Deductive (FeTi)**: $\Phi_{UEUE} = \mathcal{U} \circ \mathcal{E} \circ \mathcal{U} \circ \mathcal{E}$
- **Inductive (TeFi)**: $\Phi_{EUEU} = \mathcal{E} \circ \mathcal{U} \circ \mathcal{E} \circ \mathcal{U}$

Where $\mathcal{E}$ is the dissipative generator (Se/Ni class) and $\mathcal{U}$ is the unitary generator (Ne/Si class).

---

## Axis 3: Fiber vs Base-Lift (Inner vs Outer)

**Source:** geometry spine `AXIS_0_1_2_QIT_MATH.md`

**QIT definition:** Ax3 distinguishes whether the stage operates on a **density-stationary** path (inner/fiber) or a **density-traversing** path (outer/base-lift) on S³.

| Object | Pure Math | Meaning |
|---|---|---|
| fiber loop | $\gamma_f^s(u) = \psi_s(\phi_0+u, \chi_0; \eta_0)$ | phase-only loop; density-blind |
| base-lift loop | $\gamma_b^s(u) = \psi_s(\phi_0 - \cos(2\eta_0)u,\ \chi_0+u;\ \eta_0)$ | horizontal lifted; traverses torus |
| horizontal condition | $\mathcal{A}(\dot\gamma_b^s) = 0$ | $\mathcal{A} = d\phi + \cos(2\eta)\,d\chi$ |
| fiber density | $\rho_f^s(u) = \|\gamma_f^s(u)\rangle\langle\gamma_f^s(u)\| = \rho_f^s(0)$ | **PATH-INVARIANT** |
| base density | $\rho_b^s(u) = \tfrac{1}{2}(I + \vec r(\chi_0+u, \eta_0)\cdot\vec\sigma)$ | **CHANGES with u** |

| Class | Criterion | Label |
|---|---|---|
| inner | $\rho(u) = \rho(0)$ for all $u$ | fiber: density-stationary |
| outer | $\rho(u) \neq \rho(0)$ in general | base-lift: density-traversing |

**Executable evidence:** `sim_Ax3_density_path.py`

---

## Axis 5: T-kernel vs F-kernel (Dephasing vs Rotation)

**Source:** `v5_OPERATOR_MATH_LEDGER.md` — directly derivable

**QIT definition:** Ax5 distinguishes **dissipative dephasing channels** (T) from **unitary rotation channels** (F) in the subcycle operator family.

| Operator | Channel | Generator | Ax5 class |
|---|---|---|---|
| Ti | $(1-q_1)\rho + q_1(P_0\rho P_0 + P_1\rho P_1)$ | $\mathcal{L}_1 = \frac{\kappa_1}{2}(\sigma_z\rho\sigma_z - \rho)$ | T: $\sigma_z$ dephasing |
| Te | $(1-q_2)\rho + q_2(Q_+\rho Q_+ + Q_-\rho Q_-)$ | $\mathcal{L}_2 = \frac{\kappa_2}{2}(\sigma_x\rho\sigma_x - \rho)$ | T: $\sigma_x$ dephasing |
| Fi | $U_x(\theta)\rho U_x(\theta)^\dagger$ | $\mathcal{L}_3 = -i[\frac{\omega_3}{2}\sigma_x, \rho]$ | F: x-axis rotation |
| Fe | $U_z(\phi)\rho U_z(\phi)^\dagger$ | $\mathcal{L}_4 = -i[\frac{\omega_4}{2}\sigma_z, \rho]$ | F: z-axis rotation |

**Operator-terrain affinity rule:** Ax5 × Ax2 → unique operator identity.
Ti, Fi pair with direct terrains (Se, Ne, Ax2=direct); Te, Fe pair with conjugated terrains (Ni, Si, Ax2=conjugated).

> ✅ **Runtime corrections applied 2026-03-29:** `apply_Fe` → U_z(φ) rotation, `apply_Te` → σ_x dephasing, `apply_Fi` → U_x(θ) rotation. All three corrected per locked ledger. `sim_Ax5_TF_kernel.py` T7 confirms runtime and locked agree. `engine_core.py` kwargs updated (`dt`→`phi`, `angle`→`q`).

**Executable evidence:** `sim_Ax5_TF_kernel.py`

---

## Binarization Rule: Φ₀ → χ₀ (Ax0 closure)

The discrete binarization follows directly from the torus latitude threshold:

    χ₀ = sgn(r_z) = sgn(cos(2η))

where $r_z = \cos^2\eta - \sin^2\eta = \cos(2\eta)$ is the z-component of the Bloch vector of the orbit-average state $\bar\rho(\eta)$.

**Compatibility with χ₁χ₂:**

| Terrain | χ₁ | χ₂ | χ₁χ₂ | sgn(r_z) | Consistent |
|---|---|---|---|---|---|
| Se | +1 | -1 | -1 | -1 (S-type, lower hemisphere) | ✓ |
| Ne | -1 | -1 | +1 | +1 (N-type, upper hemisphere) | ✓ |
| Ni | +1 | +1 | +1 | +1 (N-type, drives to |0⟩=north pole) | ✓ |
| Si | -1 | +1 | -1 | -1 (S-type, lower hemisphere) | ✓ |

**Also compatible** with the coherent information form $\chi_0 = \text{sgn}(I_c(A\rangle B))$ from `AXIS_0_1_2_QIT_MATH.md` — both give the same N/S split. The torus form is geometrically grounded; the coherent-information form is the QIT-native version.

---

## 64-Address Annotation

Full 64-microstep address table with all axis annotations is produced and verified by `sim_64_address_audit.py`. Key result: all 64 `(stage_id, op_slot)` primary keys are unique; Ax6 = Ax0 ⊕ Ax3 (XOR in binary / $b_6 = -b_0 b_3$ in ±1) holds for every entry.

---

## Current Status

| Axis | Identification | Status |
|---|---|---|
| **Ax0** | geometric seat at $\eta$ plus hemisphere threshold $\text{sgn}(r_z)$ | geometry lock only; bridge/cut still open |
| **Ax1** | $U$ vs $NU$ terrain class (derived: Ax0 × Ax2) | **LOCKED (derived)** |
| **Ax2** | Weyl Interaction Picture co-rotation $V_s = e^{-iH_su}$ | **LOCKED** |
| **Ax3** | Fiber ($d\rho=0$) vs Base ($d\rho \neq 0$) | Geometry-locked |
| **Ax4** | $\Phi_{UEUE}$ vs $\Phi_{EUEU}$ ordering (derived: Ax3 × engine) | **LOCKED (derived)** |
| **Ax5** | T={Ti,Te} dephasing / F={Fi,Fe} rotation | **LOCKED** |
| **Ax6** | Derived: $b_6 = -b_0 b_3$ (Ax0 × Ax3) | **PROVEN** |

**Open issues:**
- Exact Φ₀ numerical value per terrain type depends on bridge Ξ choice
