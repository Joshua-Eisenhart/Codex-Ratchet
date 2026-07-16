# The ratchet and the manifold — actual mathematics

Date: 2026-07-11. No personal notation (the Se/Si/Ne/Ni labels are the owner's private shorthand and are
**not** testable objects — they do not appear here). No downstream "axes 1–6" (those matter only for a
finished manifold). This document is the **ratchet mechanism** and the **manifold's depth**, in real math,
every number computed in-session. Claim ceiling: `scratch_diagnostic` — a realization under the installed
complex-qubit carrier, not a proof the carrier is globally forced.

Root primitive: **constrained distinguishability**. The measure is the Umegaki relative entropy
S(ρ‖σ) = Tr[ρ(log ρ − log σ)] (nats). Everything below is built from that one quantity.

---

## 1. The pawl — the ratchet's one-way tooth = the data-processing inequality (DPI)

For every completely-positive trace-preserving (CPTP) map Φ:  **S(Φρ‖Φσ) ≤ S(ρ‖σ)**.
Physical evolution can only *lose* or *preserve* distinguishability; it can never spontaneously create it.

Computed (ρ, σ two qubit states, S(ρ‖σ) = 0.155704 nats):

| map | S after | behaviour |
|---|---|---|
| amplitude damping (CPTP) | 0.099667 | **contracts** |
| depolarizing (CPTP) | 0.052900 | **contracts** |
| unitary rotation (reversible) | 0.155704 | **preserved exactly** |

Recovering lost distinguishability requires the inverse channel, which is **not** CPTP — so there is no
physical "slip back." That monotone-under-forward, blocked-reverse asymmetry **is** the pawl. It is not a
metaphor: it is the DPI, and equality is exactly Petz recoverability.

## 2. The drive — why the ratchet advances = the relative-entropy gradient

A step is a genuine advance only where distinguishability has a nonzero gradient toward demand-closure.
Iterating a CPTP channel with fixed point ρ* (here maximally mixed), S(ρ_n‖ρ*) falls monotonically and its
step-gradient vanishes at closure:

```
 n :  S(rho_n||rho*)   gradient
 1 :   0.066956       -0.127870
 2 :   0.023750       -0.043206
 3 :   0.008506       -0.015244
 4 :   0.003057       -0.005450
 5 :   0.001100       -0.001957
 ...                   -> 0
```

**No gradient → no ratchet.** At the fixed point the drive is exactly 0 and the ratchet correctly refuses to
advance. This is the drive law as arithmetic, not doctrine.

## 3. The manifold's core identity — entropy IS geometry (not entropy running on geometry)

The unique monotone Riemannian metric attached to relative entropy is the **Kubo–Mori–Bogoliubov (BKM)**
metric, and it **equals the Hessian of S(·‖·)**. Re-derived here two independent ways on a state family
(Bloch radius 0.8, tangent in the x–z plane, at θ₀ = 0.6):

- BKM (Kubo–Mori integral) g_BKM = ∫₀¹ Tr[(dρ) ρ^{−s} (dρ) ρ^{−(1−s)}] ds = **0.87888983**
- Hessian ∂²/∂θ² S(ρ(θ)‖ρ₀) = **0.87888980**,  |difference| = **2.6×10⁻⁸**

They are the **same tensor**. The "surface" of the manifold and the entropy on it are one object. Its
monotone contraction under CPTP is the infinitesimal form of §1's DPI — the geometry and the pawl are the
same fact seen twice. (Established mathematics: Tomita–Takesaki modular theory / BKM; the ownable part is
the terrain-level rendering, not the identity itself.)

---

## 4. How deep the manifold ratchets — MSS on the Cayley–Dickson tower

"As deeply ratcheted as possible" is a precise question: how far up the normed-division-algebra tower do the
constraints **force** the carrier? The constraints are F01 (finiteness), N01 (noncommutativity), and — only
if ever forced — T01 (nonassociativity). Measured algebra properties (200-sample averages):

| level | dim | commutative? | associative? | forced by |
|---|---|---|---|---|
| ℝ reals | 1 | yes | yes | — |
| ℂ complex | 2 | yes | yes | the qubit amplitude field |
| ℍ quaternions | 4 | **no** (⟨‖[a,b]‖⟩ = 4.003) | yes (⟨assoc⟩ = 1.1×10⁻¹⁵) | **N01 forces the climb to here** |
| 𝕆 octonions | 8 | no (12.38) | **no** (⟨assoc⟩ = 22.42) | needs a forced T01 |

**N01 forces the climb up to ℍ** — and ℍ's imaginary part is exactly su(2), the qubit's Lie algebra. It does
**not** force octonions.

## 5. The honest floor — the qubit bracket is Lie, octonions are Malcev

The decisive check on whether the ratchet must go past ℍ:

- su(2) = Im(ℍ) Jacobiator ‖[[X,Y],Z] + cyc‖ = **0.0** → Jacobi holds → **Lie algebra** (associative-derived).
- Im(𝕆) Jacobiator = **12.0** → Jacobi **fails** → **Malcev**, not Lie.

Every bracket the qubit engine can form is a matrix commutator, which is always Lie. It **never** realizes a
Malcev bracket. Therefore octonions / nonassociativity are **constructible but not forced**: the manifold
ratchets down to the **complex-qubit entropic geometry (ℂ carrier, ℍ = su(2) dynamics, BKM = relative-entropy
metric, DPI pawl) and stops there.** Going deeper would require exhibiting a demand whose closure needs a
Malcev bracket — none is present. That is the honest maximal depth, stated as a theorem-shaped claim with its
own falsifier (produce the forced Malcev demand and the floor moves).

**System-size depth** (orthogonal to carrier depth): distinguishing a generic pair of n-qubit states needs
all 4ⁿ−1 Pauli measurement axes; any fixed handful of single-qubit bases resolves a vanishing fraction as n
grows — which is *why* the model needs ≥3 qubits (an 8-dim space) for full tomographic distinguishability.

---

## Bottom line
The ratchet is three pieces of standard quantum information geometry, computed here, not asserted:
**pawl = DPI** (§1), **drive = relative-entropy gradient** (§2), **surface = BKM = Hessian of relative
entropy** (§3). Its maximal forced depth is the **complex qubit with su(2) Lie dynamics** (§4–5): N01 forces
ℂ→ℍ, nothing present forces ℍ→𝕆. The whole construction is `scratch_diagnostic` — a realization under the
installed carrier; the open dig is whether any demand forces the Malcev/octonion rung or the ℂ-qubit carrier
itself.
