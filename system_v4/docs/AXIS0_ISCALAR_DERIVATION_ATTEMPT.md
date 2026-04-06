# Axis 0 — i-Scalar Derivation Attempt

**Date:** 2026-03-30
**Status:** EXPLORATION — probe-backed numerics with proposal-facing interpretation.
  Not yet a formal derivation from RC-1 + RC-2.
**Sources:** sim_axis0_orbit_phase_alignment.py, engine_core GA0_OFFSET constants,
  geometric analysis of Hopf coarse-graining.

---

## 1. What the i-Scalar Is Supposed to Be

From AXIS0_ENTROPIC_MONISM_AXIS_MAP.md:
> Dark energy = time = universal clock. The i-scalar is the frame-independent
> entropy rate. It should be derivable from RC-1 + RC-2 as the local entropy clock.

The i-scalar must be:
- Frame-independent (same across engine types 1 and 2)
- Derivable from first principles (not just an empirical fit)
- Connected to the "universal clock" role of dark energy in EM

---

## 2. Attractor Equilibrium: ga0* ≈ 0.50

**Observed (both engine types, all torus values):**

| Engine | ga0_mean | ga0_std |
|---|---|---|
| Type 1 | 0.4973 | 0.1436 |
| Type 2 | 0.4967 | 0.1567 |

The mean is strikingly stable at 0.497 ≈ 0.5 across engine type and torus latitude.

**Derivation of ga0*:**

The ga0 update rule is a target-seeking exponential blend:
```
ga0_after = ga0_before + α × (ga0_base + GA0_OFFSET_op - ga0_before)
```

At attractor equilibrium, the time-average of Δga0 over one full EC-3 cycle = 0.
For 4 operators (Ti, Fe, Te, Fi) with the same base:
```
Σ_i α (ga0_base + GA0_OFFSET_i - ga0*) = 0
→ 4 (ga0_base - ga0*) + Σ_i GA0_OFFSET_i = 0
→ ga0* = ga0_base + Σ_i GA0_OFFSET_i / 4
```

From engine_core: GA0_OFFSET = {Ti: −0.25, Fe: +0.05, Te: +0.20, Fi: −0.10}
Sum = −0.25 + 0.05 + 0.20 − 0.10 = −0.10

Therefore: **ga0* = ga0_base − 0.025**

With ga0_base ≈ 0.525 (blended terrain): ga0* ≈ 0.50 ✓

This is a **self-consistency derivation of ga0*** from the GA0_OFFSET constants.
The 0.5 attractor is not a coincidence — it follows from the balance of the four
operator offsets. Specifically, the sum of the four GA0_OFFSETs (−0.10) determines
the small shift below the terrain base.

---

## 3. Self-Consistent Coarse-Graining

The Hopf fiber coarse-graining is governed by:
```
n_samples = 1 + round(7 × ga0)
axis0_blend = strength × (0.05 + 0.30 × ga0)
```

At the attractor equilibrium ga0* ≈ 0.497:
```
n_samples(ga0*) = 1 + round(7 × 0.497) = 1 + round(3.479) = 1 + 3 = 4
```

**4 = the EC-3 cycle length (Ti→Fe→Te→Fi).**

The coarse-graining is SELF-CONSISTENT: at the entropy equilibrium, the fiber is
sampled at exactly 1 sample per operator in the EC-3 cycle. The system samples
itself at the rate of its own operator sequence.

Interpretation in EM:
> The universal clock ticks once per EC-3 operator. At the attractor, the entropy
> level and the geometric sampling depth are in exact resonance: n_samples = 4 = |cycle|.
> The "rate" at which entropy couples to geometry is 1 step/operator.

---

## 4. Candidate i-Scalar Values

Three candidate formalizations of the i-scalar emerge from this analysis.

### 4.1 The equilibrium entropy level: ga0* ≈ 0.50

**Formula:** ga0* = ga0_base + Σ(GA0_OFFSETs) / 4 = ga0_base − 0.025

**Interpretation:** The i-scalar IS the equilibrium entropy level — the universal
constant around which all engine trajectories oscillate regardless of torus position
or engine type. This is the "cosmological constant" of the entropy dynamics.

**EM reading:** Dark energy = the entropy equilibrium that the universe oscillates
around. The i-scalar = 0.5 = the half-maximum entropy point. In EM, space=entropy, so
the universe oscillates around the half-max entropy point — a tension between
maximum expansion (S=max, η=π/4 Clifford torus) and compression (S→0).

**Verdict:** Derivable from GA0_OFFSETs + terrain base. Not yet formally derived
from RC-1 + RC-2, but the connection to the operator algebra is clear.

### 4.2 The coupling strength at equilibrium: κ ≈ 0.20

**Formula:** κ = 0.05 + 0.30 × ga0* = 0.05 + 0.30 × 0.50 = 0.20

This is the axis0_blend / strength ratio at the attractor. It is independent of
torus position and engine type:
- Engine 1: 0.1992
- Engine 2: 0.1990

**Interpretation:** κ = 0.20 is the rate at which entropy (ga0) couples to
geometry (Hopf fiber coarse-graining) at the universal attractor. It measures
how much the entropy level CHANGES the effective sampling of the fiber.

**EM reading:** κ is the dark energy coupling constant — the coupling between
the entropy field (space) and the information structure (coarse-graining depth).
It plays the role of G (gravitational constant) in classical physics: a universal
coupling that sets the strength of the entropy→geometry interaction.

**Verdict:** The most universal and "constant-like" of the three candidates.
Formally κ = 0.05 + 0.30 × ga0*, which reduces to a function of the GA0_OFFSETs.

### 4.3 The mean entropy flux per step: ε ≈ 0.08 bits/step

**Observed:**
- Engine 1: 0.0775 bits/step
- Engine 2: 0.0805 bits/step

**Interpretation:** The mean |Δga0| per operator step = the rate of entropy
production/consumption per engine tick. This is the "jk fuzz amplitude" — the
mean-square entropy fluctuation that makes the trajectory look stochastic.

**Verdict:** Less universal than κ (slight engine-type dependence). But it is the
most directly physical: it is the entropy flux, the quantity that makes the
engine irreversible.

---

## 5. The Clifford Connection

The Clifford torus (η = π/4) has maximum torus entropy: S(π/4) = log 2 ≈ 0.693.
This is the MAXIMUM ENTROPY point on the torus.

Yet ga0_mean ≈ 0.5 even on Clifford. This means the spinor entropy (ga0) is
independent of the torus entropy at the attractor. The equilibrium ga0* ≈ 0.5 is
a property of the OPERATOR DYNAMICS (GA0_OFFSETs), not of the torus position.

In EM: The "universal clock" (i-scalar) is operator-algebraic, not geometric.
The dark energy rate is set by the operator balance (GA0_OFFSETs sum to −0.10),
not by the spatial entropy configuration (torus η).

This separates two kinds of entropy in the EM framework:
- **Torus entropy S(η)**: the spatial entropy = space configuration (Ax0 geometry)
- **Spinor entropy ga0**: the dynamical entropy = operator balance (Ax0 dynamics)

The i-scalar κ ≈ 0.20 is about the spinor entropy coupling to geometry, not the
geometry itself.

---

## 6. Formal Derivation Path (What Still Needs RC-1 + RC-2)

A complete derivation of the i-scalar from RC-1 + RC-2 requires:

| Step | Content | Status |
|---|---|---|
| RC-1 constraint | Hopf fibration as the spatial entropy gradient field | Partially derived |
| RC-2 constraint | EC-3 cycle as the operator algebra's closure condition | Partially derived |
| GA0_OFFSET balance | Derive -0.10 sum from EC-3 axiom | OPEN |
| ga0* derivation | Show ga0* = ga0_base − 0.025 from RC-1 + RC-2 | OPEN (numeric confirmed) |
| κ = 0.20 | Derive coupling from entropy field equations | OPEN |
| n_samples = 4 at ga0* | Derive resonance condition from fiber geometry | OPEN |

The numeric result (ga0* ≈ 0.50, κ ≈ 0.20, n_samples* = 4) is fully confirmed.
The derivation path from first principles is the remaining work.

---

## 7. Anti-Smoothing

- ga0* ≈ 0.5 is derived from GA0_OFFSET balance, NOT from torus entropy.
  The two entropies (spinor and torus) are DECOUPLED at the attractor.
- κ ≈ 0.20 is a function of ga0*, not an independent constant.
  It is not "the cosmological constant" — it is a derived quantity.
- The n_samples = 4 resonance is suggestive but depends on the specific value
  of the "7" coefficient in the coarse-graining formula. That coefficient is
  not yet derived from first principles.
- The "EM reading" sections above are proposal-facing interpretations.
  They are candidate framings, not canon claims.
