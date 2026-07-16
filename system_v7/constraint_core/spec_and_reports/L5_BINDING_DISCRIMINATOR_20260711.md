# L5 settled: shell structure binds a second coordinate under response, not static readout

Date 2026-07-11. This closes the open L5 dig the v0.5 audit left. Every number computed by running
`sims_and_scripts/manifold_L5_binding_discriminator_sim.py`. Ceiling: `scratch_diagnostic`.

## The problem the audit found (real, not papered over)
The v0.5 data-driven L5 re-audit measured whether nested-shell structure beats a plain scalar at
predicting four marginal readouts, held out. It found them **indistinguishable**:

| predictor | held-out pooled RMSE (file, seed 0) |
|---|---|
| polynomial_degree3 (plain cubic) | 0.0143 — best |
| scalar_stratum | 0.0588 |
| nested_shell_structured | 0.0588 — identical to scalar |
| constant_mean (must lose) | 0.3707 ✓ |
| deliberate_overfit (must flip) | 21.98 ✓ |

Verdict in the file: `INDISTINGUISHABLE_WITHIN_FROZEN_TOLERANCE`. **Why** (the part the status report didn't
show): that obligation is **one-dimensional by construction.** For a pure 2-qubit state, the marginal is
ρ_A(η) = ½(I + |cos2η| ẑ·σ) — radius, marginal entropy, purity, and negativity are all functions of the
**single** Schmidt angle η. So a scalar in the radius wins trivially; the shell geometry has no second
coordinate to bind. This was not a failure of the geometry — it was the wrong obligation.

## The obligation that can bind (built honestly, non-circular)
Give the marginal a genuine second coordinate — orientation:
```
   rho_A(eta,phi) = 1/2 ( I + r(eta) * n(phi).sigma ),   r(eta) = |cos 2eta|  (shell radius),
   n(phi) = (sin phi, 0, cos phi)                          (Schmidt-basis orientation)
```
This is exactly the reduced state of a pure 2-qubit state with Schmidt angle η and local basis rotated by φ.
The obligation is a **physical response**, not an answer key: apply a FIXED z-dephasing channel
D_z(ρ) = ½(ρ + ZρZ) and predict the entropy change **dS = S(D_z ρ) − S(ρ)**. Because D_z is basis-selective,
dS depends on **both** the radius and the orientation — a physics fact, imposed by no hand-tuned target.

Two predictors, fit on 40 points, scored on 20 held out:
- **SCALAR** — dS ~ cubic in r (radius/shell only)
- **STRUCTURED** — dS ~ cubic in (r, r·cosφ) (radius + orientation)

## Result (computed)
| quantity | value |
|---|---|
| SCALAR (radius only) held-out RMSE | **0.2540** |
| STRUCTURED (radius+orientation) held-out RMSE | **0.0227** |
| improvement | **11.2×** — orientation binds |

**The second coordinate is earned.** Once you probe *response* rather than a static readout, a scalar in the
radius is no longer sufficient; the manifold is genuinely ≥2-dimensional.

## Controls (each must fire — the gate is not a rubber stamp)
| control | manipulation | result |
|---|---|---|
| **erase orientation** | set all φ=0 → dS depends on r only | scalar 0.0000 == structured 0.0000 → **collapse** (proves φ was carrying the advantage, not extra parameters) |
| **overfit** | exact 2-D RBF interpolant on train | fit RMSE 3.4×10⁻¹⁷, held-out 0.32 → **flips** (the gate is held-out-honest) |
| **scalar not crippled** | scalar given full cubic flexibility in r | still 0.2540 → it genuinely cannot reach the orientation-dependent response |

## What this settles, and its honest scope
- The v0.5 "shell = scalar" tie was an artifact of a 1-D obligation. Under a 2-D response obligation the
  geometry binds: **orientation (Schmidt-basis direction) is a second forced coordinate.**
- Scope, stated plainly: the coordinate that binds is **orientation, not radius-nesting.** Radius alone stays
  scalar-sufficient (consistent with the audit). The earned claim is narrow and exact: the L5 marginal
  manifold is ≥2-D once response is probed — it is not a vindication of "nested shells" as such.
- This is the discriminator the audit file itself asked for ("an obligation where shell structure could
  bind — perturbation response"). It is now built, run, and gated.
