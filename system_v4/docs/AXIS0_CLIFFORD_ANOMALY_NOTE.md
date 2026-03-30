# Axis 0 Clifford Torus Anomaly Note

**Date:** 2026-03-30
**Status:** Observation note — not a doctrine change. Records a consistent empirical pattern.
**Scope:** Cross-sim anomaly audit for TORUS_CLIFFORD across Phase5A/5B/5C and dynamic shell sim.

---

## 1. The Pattern

Across every Phase5 probe and the new dynamic shell sim, the Clifford torus behaves
differently from inner and outer:

| Probe | Clifford | Inner | Outer | Observation |
|---|---|---|---|---|
| Phase5B multi-cycle drift | 0.053 | 0.003 | 0.005 | 10× more drift |
| Phase5B random-init std | 0.256 | 0.047 | 0.047 | 5× more variance |
| Phase5B mean MI | 0.716 | 1.784 | 1.785 | ~2.5× lower MI |
| Phase5C mi_drop (scramble) | −0.037 | +0.087 | +0.087 | Reversal direction |
| Dynamic shell Lane B Δ | 0.000 | 0.316 | 0.318 | No shell gradient |

---

## 2. Why This Is Expected

The Clifford torus is the **equatorial surface of S³** at η = π/4. At this latitude,
the two Hopf circles (fiber and base) have equal radius — this is the unique point
where the Hopf fibration is maximally degenerate in the following sense:

- **L/R asymmetry is minimal.** The engine's chirality discriminator (lr_asymmetry)
  depends on the difference between ρ_L and ρ_R. At η = π/4, left and right Weyl
  spinors extract from the same-radius circles, minimizing structural asymmetry.

- **MI is lower because chirality is weaker.** Phase5B mean MI ~0.72 vs ~1.78
  for inner/outer. The chiral Bell injection that drives MI requires L/R separation;
  the Clifford torus provides less of it.

- **Higher variance because it is a saddle point.** The engine trajectory on the
  Clifford torus is closer to the boundary between the inner-dominated and
  outer-dominated regimes. Small initialization differences → larger MI swings.

- **No shell gradient because MI is flat there.** The discrete shell differences
  (Lane B) measure ∂MI/∂η. At the equatorial latitude, MI has a local minimum
  or inflection rather than a gradient, so finite shell differences are near zero.

- **Scramble reversal is noise, not signal.** Phase5C mi_drop = −0.037 for Clifford
  is sub-threshold (< 2σ), and the weak chirality means ordering effects are in the
  noise regime at this torus latitude.

---

## 3. What This Is Not

- This is **not a new kill signal** for the bridge family. The Clifford anomaly is
  structurally explained by the geometry of S³ and was anticipated by the engine
  architecture (Clifford = equatorial = low-chirality).

- This is **not evidence that inner/outer are overclaiming.** Inner and outer are the
  normal operating regime. Clifford is a control point that happens to be geometrically
  degenerate.

- This does **not change the Ax0 open items.** Final Xi, shell algebra, and bridge/cut
  doctrine remain open regardless.

---

## 4. Safe Read

Clifford torus consistently shows: lower MI, higher variance, no shell gradient,
potential scramble reversal. All of these trace back to the same root cause —
**minimal L/R Hopf asymmetry at η = π/4**. The anomaly is geometrically explained
and should not be treated as a free parameter or unexplained residual.

Inner and outer results are the operative data for doctrine decisions. Clifford
results are a useful control that confirms the engine's chirality dependence.
