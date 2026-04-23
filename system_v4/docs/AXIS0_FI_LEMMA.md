# Axis 0 — Fi Algebraic Invariance Lemma

**Date:** 2026-03-30
**Status:** PROOF — analytically derived, probe-confirmed (1995/1995 universally).
**Source:** sim_axis0_coarising_stress_test.py Level 1 + Level 2 results.

---

## 1. Statement

> **Fi Lemma:** For any pair of density matrices (ρ_L, ρ_R), the Fi operator
> (U_x(θ) with right-spinor conjugate dynamics) leaves lr_asym exactly invariant:
>
>   lr_asym(Fi(ρ_L), Fi_conj(ρ_R)) = lr_asym(ρ_L, ρ_R)
>
> Proof: algebraic. Confirmed numerically: 1995/1995 trials (100.0%), zero failures.

---

## 2. Proof

### 2.1 Fi on the left spinor

Fi is U_x(θ):

```
U_x(θ) = cos(θ/2) I − i sin(θ/2) σ_x
```

Left spinor: ρ_L → ρ_L' = U_x(θ) ρ_L U_x†(θ)

### 2.2 Fi on the right spinor (conjugate dynamics)

The right spinor uses the conjugate rule from engine_core:

```python
rho_conj = σ_x @ rho_R @ σ_x
rho_conj = apply_Fi(rho_conj, ...)
rho_R_new = σ_x @ rho_conj @ σ_x
```

That is: ρ_R' = σ_x U_x(θ) σ_x ρ_R σ_x U_x†(θ) σ_x

### 2.3 Key identity: σ_x commutes with U_x

```
σ_x U_x(θ) σ_x = σ_x [cos(θ/2) I − i sin(θ/2) σ_x] σ_x
               = cos(θ/2) (σ_x I σ_x) − i sin(θ/2) (σ_x σ_x σ_x)
               = cos(θ/2) I − i sin(θ/2) σ_x        [since σ_x² = I]
               = U_x(θ)
```

### 2.4 Right spinor gets the same unitary

Substituting the identity:

```
ρ_R' = σ_x U_x σ_x · ρ_R · σ_x U_x† σ_x
      = U_x(θ) ρ_R U_x†(θ)
```

Both left and right spinors undergo the same U_x(θ) rotation.

### 2.5 lr_asym is preserved

```
lr_asym(ρ_L, ρ_R) = ½ ‖bloch(ρ_L) − bloch(ρ_R)‖₂
```

Since U_x(θ) is unitary, its action on Bloch vectors is an orthogonal
rotation R_x(θ) ∈ SO(3) (rotation by 2θ around the x-axis):

```
bloch(U_x ρ_L U_x†) = R_x(θ) · bloch(ρ_L)
bloch(U_x ρ_R U_x†) = R_x(θ) · bloch(ρ_R)
```

Therefore:

```
bloch(ρ_L') − bloch(ρ_R') = R_x(θ) · [bloch(ρ_L) − bloch(ρ_R)]
‖bloch(ρ_L') − bloch(ρ_R')‖₂ = ‖bloch(ρ_L) − bloch(ρ_R)‖₂   [R_x isometry]
```

So lr_asym(ρ_L', ρ_R') = lr_asym(ρ_L, ρ_R).  **QED.**

---

## 3. Corollaries

### 3.1 Bridge MI is also invariant under Fi

lr_asym is the sole input to the Bell injection fraction in bridge_mi:

```
rho_AB = (1 − p) (ρ_L ⊗ ρ_R) + p |ψ−⟩⟨ψ−|    where p = lr_asym
```

Since lr_asym is unchanged, the bridge MI is unchanged by Fi.
Therefore: sign(ΔMI) = 0 under Fi, and the probe counts this as "agree"
(neutral step — Δlr_asym < ε treated as agreement in the stress test).

### 3.2 Level 2 universality (1980/1980)

Bridge MI universality at Level 2 (direct ΔMI sign test): 100.0% agreement,
0 failures. The Fi step leaves the bridge unchanged — confirmed independently.

### 3.3 ga0 can still change under Fi

The ga0 update is governed by:

```
ga0_target = ga0_base + GA0_OFFSET["Fi"]   (GA0_OFFSET["Fi"] = −0.10)
Δga0 = α (ga0_target − ga0_before)
```

This is a target-seeking update independent of the quantum state. When
ga0_before > ga0_target, Δga0 < 0 (contraction). lr_asym = const → ΔMI = 0.
The probe classifies zero-change as "agree," so the 100% rate holds.

**Note:** Fi can be in a sign-mismatch regime if ΔMI is nonzero from the
cross-temporal bridge (L_after ⊗ R_before pairing). The instantaneous invariance
proven here is for the same-step lr_asym. The actual engine bridge may differ.

---

## 4. Structural position

Fi is the *only* operator that is algebraically lr_asym invariant:

| Operator | lr_asym universality | Reason |
|---|---|---|
| Ti | ✗ (80.2%) | Lüders dephasing: z-component asymmetry state-dependent |
| Fe | ✗ (51.1%) | U_z(φ): left/right conjugations differ in z-phase |
| Te | ✗ (35.8%) | σ_x dephasing: conjugate flips polarity → reversed Bloch mixing |
| **Fi** | **✓ (100%)** | **U_x: σ_x commutes with U_x → identical left/right unitary** |

The key algebraic fact: σ_x is the generator direction of U_x, so conjugation by σ_x
(the right-spinor conjugate map for F-kernel operators) leaves U_x exactly invariant.
Fe uses U_z, whose generator (σ_z) does NOT commute with σ_x under conjugation —
hence Fe breaks the invariance.

---

## 5. Implications for OPEN-1

The Fi lemma establishes the simplest half of the co-arising proof:
- Fi step: Δlr_asym = 0, ΔMI_instantaneous = 0 — the step is neutral.
- The empirical sign(Δga0) = sign(ΔMI) for Fi on the trajectory reflects the
  cross-temporal bridge and the trajectory structure, not the instantaneous operator.
- A full algebraic proof of OPEN-1 must invoke the attractor conditions, not just Fi.

The Fi result DOES constrain the proof structure: the algebraic part (Fi invariance)
is already closed. The remaining open piece is Ti/Fe/Te, which require the
attractor trajectory as a precondition.
