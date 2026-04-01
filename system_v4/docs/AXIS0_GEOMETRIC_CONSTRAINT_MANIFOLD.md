# Axis 0 and Geometric Constraint Manifold

**Date:** 2026-03-29  
**Status:** Working packet. Direct geometry is source-backed and probe-backed. `Axis 0` kernel family is source-backed. The bridge `Xi : geometry/history -> rho_AB` and the exact cut `A|B` are still open.

---

## Scope

- [AXIS0_ACTIVE_PACKET_INDEX.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_ACTIVE_PACKET_INDEX.md) is the compact entrypoint for the active `Axis 0` controller, owner, support, and geometry-side packet stack.

This file isolates only:

- the geometric constraint manifold
- the current `Axis 0` kernel family
- the open bridge from geometry/history into a cut state
- the strongest executable evidence

It does not try to settle `Axis 3-6`.

---

## Direct Geometry Spine

These objects are the tightest source-backed geometry in the screenshot packet and local probe layer.

| Layer | Pure math | Meaning |
|---|---|---|
| carrier | `S^3 = { psi in C^2 : ||psi|| = 1 }` | normalized spinor carrier |
| Hopf map | `pi(psi) = psi^dagger sigma_vec psi in S^2` | Bloch projection |
| density reduction | `rho(psi) = |psi><psi| = 1/2 (I + r_vec . sigma_vec)` | density-state image of a carrier point |
| torus stratum | `T_eta = { (e^{i alpha} cos eta, e^{i beta} sin eta) : alpha,beta in S^1 } subset S^3` | one nested Hopf torus |
| Hopf connection | `A = -i psi^dagger d psi = d phi + cos(2 eta) d chi` | separates fiber and horizontal motion |
| fiber loop | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | vertical/Hopf-fiber loop |
| base loop | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | horizontal lifted-base loop |
| horizontal condition | `A(dot gamma_base^s) = 0` | source-tight base-loop constraint |
| fiber density path | `rho_f^s(u) = |gamma_f^s(u)><gamma_f^s(u)| = rho_f^s(0)` | density-stationary loop family |
| base density path | `rho_b^s(u) = |gamma_base^s(u)><gamma_base^s(u)|` | density-traversing loop family |

Two points matter here:

1. `fiber/base` is the universal geometry language.
2. `inner/outer` should be treated as an engine-indexed overlay, not universal carrier geometry.

---

## Compiled Working Layer

These objects are useful and supported by the screenshot packet plus probes, but they are not the same thing as the direct carrier geometry.

| Layer | Pure math | Meaning |
|---|---|---|
| sheet variable | `s in {L, R}` | left/right working sheet |
| Weyl Hamiltonians | `H_L = +H_0`, `H_R = -H_0` | coherent sign flip across sheets |
| terrain law | `X_{tau,s}` | local flow law on a chosen sheet |
| operator family | `J_o` | local channel/operator map |
| precedence | `Psi_up`, `Psi_down` | composition order layer |

This is the clean separation:

- direct geometry: `S^3 -> T_eta -> gamma_fiber/gamma_base -> rho(psi)`
- compiled working layer: sheets, terrains, operators, precedence

---

## Axis 0 Role

`Axis 0` is the **external scalar field** on the constraint manifold.

This packet keeps two things separate:

- the geometric seat and diagnostics of `Axis 0`
- the later cut-state kernel family that still depends on bridge `Xi` and cut `A|B`

### Geometric Seat: $\eta \in [0, \pi/2]$

Axis 0 is seated geometrically in the $\eta$ direction of the $S^3$ manifold.

- **Pointwise Field**: $\varphi_0(x) = S(\bar{\rho}(\eta(x)))$
  - This is the entropy of the orbit-averaged density state at latitude $\eta$.
  - $\varphi_0$ is zero at the poles (pure states) and maximum at the Clifford torus ($\eta = \pi/4$).
- **Discrete Bit**: $b_0 = \text{sgn}(\cos(2\eta)) = \text{sgn}(r_z)$
  - Binarizes the manifold into North ($+1$) and South ($-1$) hemispheres.

---

## Kernel Family Ranking

### 1. Geometric Diagnostic Seat (Torus Entropy)

```text
Phi_0(eta) = S(bar_rho_eta) = -cos^2(eta) ln(cos^2(eta)) - sin^2(eta) ln(sin^2(eta))
```

Why it remains important:
- It is derived directly from the $S^3 \to S^2$ Hopf mapping.
- It provides a universal entropy coordinate for all nested tori.
- It naturally defines $\eta = \pi/4$ as the phase transition point.
- It is a geometric diagnostic, not a finished cut-state bridge theorem.

### 2. Preferred Simple Cut-State Kernel (Bipartite $I_c$)

```text
Phi_0(rho_AB) = I_c(A|B) = S(rho_B) - S(rho_AB)
```

Why it currently ranks above plain geometric diagnostics:
- It is the QIT-grounded version used for engine entropy bookkeeping.
- It matches the signed-gradient behavior required for the "negative battery" effect.
- It still depends on an admitted bridge and cut on the same stack.

Compatibility note:

- $b_0 = \text{sign}(I_c)$ may align with $b_0 = \text{sign}(r_z)$ on favored families
- that alignment does not erase the bridge/cut dependence of the QIT kernel

---

## Bridge `Xi` Update

The bridge $\Xi$ into the cut state is still open.

What this packet keeps:

- raw torus latitude is a real geometric diagnostic
- raw averaged left/right product states are honest controls
- trajectory-shaped readouts remain live as bridge-family candidates

What this packet does not claim:

- one product construction closes the bridge
- one trajectory readout is already final `Xi`
- geometry by itself is already the cut-state bridge

---

## Executable Evidence

### Geometry validity

| Probe | Result | What it supports |
|---|---|---|
| `system_v4/probes/sim_L0_s3_valid.py` | PASS | `S^3`, `SU(2)`, Hopf map, fiber preservation, Berry phase, torus coordinates, and Bloch round-trip are numerically valid |
| `system_v4/probes/hopf_manifold.py` | geometry primitives library | direct carrier geometry is implemented explicitly, not just named |

The most important fresh values from `L0_hopf_manifold_results.json` are:

- `fiber_max_deviation ~ 4.87e-16`
- `berry_phase = -pi`
- `bloch_max_error ~ 2.48e-16`

### Kernel discrimination

| Probe | Result | What it supports |
|---|---|---|
| `system_v4/probes/axis0_gradient_sim.py` | PASS | `-S(A|B)` cleanly provides the signed negative-gradient behavior |
| `system_v4/probes/axis0_path_integral_sim.py` | PASS | shell-cut / coherent-information / history-shaped `Axis 0` forms remain live |
| `system_v4/probes/axis0_correlation_sim.py` | PASS | mutual information can track build-and-burn of correlation, but only as a proxy/diagnostic |

Fresh values:

- separable state:
  - `I(A:B) = 0`
  - `S(A|B) = 1`
- Bell state:
  - `I(A:B) = 2`
  - `S(A|B) = -1`

That is the strongest simple reason to rank `-S(A|B)` above plain `I(A:B)`.

The fresh `axis0_correlation_sim.py` run is still useful, but only in the narrower sense:

- initial mixed state: `I(A:B) = 0`, `S(A|B) = 2`
- post-coupling: `I(A:B) ~ 0.1718`, `S(A|B) ~ 1.8104`
- post-burn: `I(A:B) = 0`, `S(A|B) ~ 1.9822`

So it shows correlation accumulation and burn, but it does not give the negative signed primitive that the simpler Bell-state test gives.

### Geometry interaction warning

| Probe | Result | What it warns against |
|---|---|---|
| `system_v4/probes/sim_axis_hopf_geometry.py` | mixed result | torus transport is not cleanly identical to `Axis 0` |

The strongest warning signal from that sim:

- `torus_transport x Axis 0:coarse = 0.7071` on inner and outer torus strata
- `torus_transport x Axis 0:coarse = 0.0000` on random `S^3` and Clifford torus samples

So:

- torus transport clearly matters geometrically
- but it does not behave like a universal `Axis 0` kernel by itself

### Weyl-pair caution

| Probe | Result | What it warns against |
|---|---|---|
| `system_v4/probes/sim_weyl_dof_analysis.py` | 8 independent Weyl-pair DOF clusters | the Weyl pair is a richer ambient structure than a single finished `Axis 0` cut |

---

## Best Current Lock

| Piece | Best current read |
|---|---|
| direct geometry | `S^3 -> T_eta -> gamma_fiber/gamma_base -> rho(psi)` |
| compiled working layer | Weyl sheets, terrain laws, operators, precedence |
| `Axis 0` role | external scalar field on the constraint manifold through cut-state functionals |
| best simple kernel | `-S(A|B)_rho` |
| best global form | `sum_r w_r I_c(A_r > B_r)_rho` |
| best diagnostic companion | `I(A:B)_rho` |
| missing piece | explicit `Xi` and exact cut `A|B` |

---

## Fastest Next Experiments

| Experiment | Input object | Observable | What it would settle fastest |
|---|---|---|---|
| kernel bakeoff | same small `rho_AB` family | `-S(A|B)`, `I(A:B)`, `sum_r w_r I_c` | which kernel best matches signed-gradient behavior without extra narrative |
| pointwise pullback test | `x in T_eta subset S^3` | `phi_0(x)` along fiber vs base loops | whether pointwise `Axis 0` is geometrically meaningful |
| history-vs-pointwise test | short trajectories `h(t)` | `phi_0(x_t)` vs `phi_0[h]` | whether `Axis 0` is fundamentally state-shaped or trajectory-shaped |
| `Xi` bridge bakeoff | same geometry/history sample under multiple bridge constructions | sign stability, perturbation sensitivity, loop-family stability | least arbitrary bridge family |

---

## Bottom Line

The strongest current picture is:

1. the geometric constraint manifold is real and numerically validated
2. `Axis 0` is best treated as a continuous cut-state correlation family, not a mere binary color split
3. `-S(A|B)` is the strongest simple working kernel
4. the exact bridge from geometry/history into `rho_AB` is still the unfinished part
