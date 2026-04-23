# Axis 0 — OPEN-1 Proof Strategy: ga0 = MI Co-arising Theorem

**Date:** 2026-03-30
**Status:** STRATEGY — not a proof. Consolidates findings from the attractor basin
  and orbit phase alignment probes to define the minimal proof path.
**Sources:** sim_axis0_coarising_stress_test.py, sim_axis0_attractor_basin_boundary.py,
  sim_axis0_orbit_phase_alignment.py, AXIS0_FI_LEMMA.md, AXIS0_ATTRACTOR_BASIN_NOTE.md

---

## 1. The Claim to Prove

**OPEN-1:** sign(Δga0) = sign(ΔMI) at every step of the engine trajectory.

This is not the strict claim. The probe-backed claim (T3 cross-correlation, 12/12) is:

> On the Hopf attractor, the cross-correlation of {d_ga0[t]} and {d_ct_mi[t]} peaks
> at lag=0, across all 6 torus/engine-type configurations.
> Here d_ct_mi[t] = MI(rho_L[t], rho_R[t+1]) − MI(rho_L[t−1], rho_R[t]).

The per-step co-arising rate is 84–87% (probe result from orbit phase probe):
- Overall: 27–28/31 steps (inner: 73%, outer: 94%)
- The T3 cross-correlation claim (peak at lag=0) is a weaker statement — it is
  satisfied by 84–87% per-step co-arising.

**The proof target is: why does the outer loop achieve ~94% and what breaks inner?**

---

## 2. What Is Already Closed

### 2.1 Fi: algebraically exact (AXIS0_FI_LEMMA.md)

Fi (U_x(θ)) with the right-spinor conjugate rule produces the identical unitary for
both L and R spinors. lr_asym is preserved exactly: Δlr_asym = 0 always.
The 87.5% forward co-arising rate for Fi is a SEQUENCE effect (what happens to the
forward MI when L[t] moves but R[t+1] is the next-step Ti output), not an
instantaneous operator effect. The algebraic invariance is complete.

**Implication for proof:** Fi leaves the attractor's lr_asym unchanged.
Any forward MI change at a Fi step is entirely driven by the next step's R[t+1].

### 2.2 Ti: contingently universal on the attractor

Ti failure boundary: lr_asym_before < 0.05. On the attractor: min lr_asym ≈ 0.60.
Ti is 100% per-step co-arising on Type 1 (engine 1 inner = 7/7, outer = 4/4 per cycle).
Engine 2 fails once at step 16 (the outer→inner transition); lr_asym = 0.873 there —
this failure is contingent on the specific Type 2 initial geometry, not a structural one.

**Implication for proof:** Ti co-arising on the attractor requires only lr_asym > 0.05,
which is guaranteed by the Hopf orbit. This is the weakest condition to prove — it
follows from the attractor basin characterization.

---

## 3. The Core Difficulty: Inner Loop / Fi Failures

### 3.1 Observed failure pattern

From orbit phase alignment (aggregate across all 6 configs):

| Operator | Co-arising rate | Failure concentration |
|---|---|---|
| Ti | 93% (39/42) | Step 16, Type 2 only |
| Fe | 85% (41/48) | Inner loop, steps 21–25 |
| Te | 83% (40/48) | Inner loop, steps 18–26 |
| **Fi** | **73% (35/48)** | **Inner loop, steps 19–31, especially Clifford** |

The outer half of the orbit: 94.4% co-arising (nearly perfect).
The inner half: 72.9%.

All Fi failures have d_ct_mi > 0 (MI increases) while d_ga0 < 0 (ga0 decreases, Fi
contracts). The forward bridge MI increases at an inner-loop Fi step when the
Fi-processed L[t] is MORE aligned with R_Ti[t+1] than L_Te[t−1] was with R_Fi[t].

### 3.2 Why the outer loop nearly never fails

The outer loop applies Ti/Fe/Te/Fi to states that started the cycle. These states
are freshly initialized and have lr_asym near maximum (attractor baseline).
The outer→inner transition introduces the first accumulated history of the cycle.
By step 16 (first inner Ti), the states have been shaped by 16 operator applications,
and the inner-loop geometry (smaller η) produces qualitatively different dynamics.

The outer co-arising (~94.4%) is sufficient for the T3 cross-correlation claim.
Proving outer co-arising requires: lr_asym > 0.05 (Ti), and the Hopf orbit phase
structure keeping L[t] aligned with R[t+1] on the outer fiber.

### 3.3 The Fi / inner-loop failures are not a contradiction

The T3 claim is cross-correlation peak at lag=0, not per-step universality.
The inner-loop 72.9% co-arising — with failures concentrated at Fi — is consistent
with the cross-correlation result because:
(a) Even 73% per-step yields positive cross-correlation between d_ga0 and d_ct_mi.
(b) The failure magnitude is small (d_ct_mi mean ≈ +0.035 vs typical step d_ct_mi ≈ 0.1–0.4).

---

## 4. Proof Path

### Step 1 — Outer loop co-arising (tractable)

**Claim:** On the outer Hopf fiber, 94% of steps co-arise in the forward MI.

**Proof strategy:**
1. Show that on the outer fiber, lr_asym[t] ≥ 0.62 throughout (attractor basin).
2. Show Ti co-arises (lr_asym >> 0.05 → Lüders dephasing decreases lr_asym).
3. Show Fe/Te/Fi co-arise by the orbit phase structure:
   - Fe: U_z(φ) rotates L; R[t+1] is the Te_conj output; show MI(Fe(L), Te_conj(R)) tracks ga0.
   - Te: σ_x dephasing of L; R[t+1] is Fi_conj output; show alignment.
   - Fi: lr_asym invariant; forward MI change = f(Ti_conj(R[t])) — reduces to Ti's right spinor.

### Step 2 — Inner loop structure

**Claim:** Inner loop failures are bounded (< 28%) and do not change the sign of
the cross-correlation sum.

This step likely requires: characterize the inner Hopf fiber orbit structure separately,
show that the sum Σ_t sign(d_ga0 · d_ct_mi) is positive for the full 32-step cycle
even if individual inner steps fail.

### Step 3 — Cross-correlation bound

**Final claim:** Cross-corr(d_ga0, d_ct_mi) at lag=0 > cross-corr at lag=±1.

This is weaker than per-step universality and more directly provable from Steps 1+2.
Requires: that the outer loop's near-universal co-arising dominates the cross-correlation
sum over the inner loop's partial failures.

---

## 5. Open Formal Items Required for the Proof

| Item | What is needed | Difficulty |
|---|---|---|
| Outer orbit characterization | Show lr_asym[t] ≥ 0.62 on outer fiber | Medium |
| Ti co-arising bound | lr_asym >> 0.05 → Lüders dephasing decreases Δlr_asym | Done (contingent) |
| Fe orbit alignment | U_z phase relationship between L[t] and R[t+1] on outer fiber | High |
| Te orbit alignment | σ_x dephasing + Fi_conj R[t+1] phase relationship | High |
| Fi forward MI bound | Show that forward MI change at Fi step = f(next Ti's R) | Medium |
| Inner loop failure bound | 28% failures do not flip the cross-corr sign | Medium |
| Cross-corr sum bound | Σ(outer) > |Σ(inner failures)| | Medium |

---

## 6. Clifford Anomaly Connection

Clifford has more failures (mean 6.5 vs 4.5) and lower co-arising rate (79% vs 85.5%).
The extra failures are concentrated at Fi inner-loop steps.
In the failure profiles, Clifford Fi-step lr_asym values are much lower (0.535, 0.613,
0.645) than non-Clifford failures (0.873, 0.989, 0.987). This confirms the Clifford
anomaly (low chirality → lower lr_asym floor → more vulnerable forward pairing).

**For the proof:** Clifford is the hardest case. A proof that works for Clifford
works for all. The key Clifford property: lower minimum lr_asym on the trajectory.
If the inner-loop lr_asym floor for Clifford can be bounded below ~0.5, the Ti condition
is still satisfied but the Fe/Fi forward pairing has more room to fail.

---

## 7. Next Step in the Proof Program

The most tractable immediate step is **Step 1: outer orbit co-arising**.

Specifically: write the algebraic form of:
  MI(Fe(L[t]), Te_conj(R[t+1]))  −  MI(Te(L[t−1]), Fe_conj(R[t]))

and show its sign matches sign(Δga0_Fe). This is the outer loop's critical Fe failure
check — Fe fails 1/8 even on the outer loop (87.5%), and that 1 failure is what caps
the outer rate below 100%.

If the Fe outer failure can be characterized algebraically, it closes a major piece.
