# Axis 0 and Geometric Constraint Manifold

**Date:** 2026-03-29  
**Status:** Working packet. Direct geometry is source-backed and probe-backed. `Axis 0` kernel family is source-backed. The bridge `Xi : geometry/history -> rho_AB` and the exact cut `A|B` are still open.

---

## Scope

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

`Axis 0` is not an operator and not a terrain.

The strongest source-backed role is:

`Axis 0 = external scalar field on the constraint manifold through a cut-state functional`

Pointwise shape:

```text
phi_0(x) = Phi_0(rho(x))
```

History shape:

```text
phi_0[h] = (1/T) integral_0^T sum_{cut in C} w_cut I_c(cut; rho_h(t)) dt
```

So `Axis 0` has at least two live shapes:

- pointwise pullback on the manifold
- history functional over a trajectory

Their exact unification is still open.

---

## Kernel Family Ranking

### Best simple working kernel

```text
Phi_0(rho_AB) = -S(A|B)_rho = I_c(A>B)_rho
```

Why it currently ranks first:

- it is source-backed
- it can go negative
- the local `axis0_gradient_sim.py` run cleanly separates it from plain mutual information

### Strongest global/shell-cut form

```text
Phi_0(rho) = sum_r w_r I_c(A_r > B_r)_rho
           = - sum_r w_r S(A_r|B_r)_rho
```

Why it stays live:

- it is the strongest screenshot-backed global form
- it matches the "external scalar field on M" idea better than a single fixed two-part cut

### Strong companion diagnostic

```text
I(A:B)_rho = S(rho_A) + S(rho_B) - S(rho_AB)
```

Why it is not ranked first:

- it is always non-negative
- it can track total correlation
- it does not by itself supply the signed "negative battery" behavior

### Current ranking

| Role | Pure math | Current status |
|---|---|---|
| primary simple kernel | `-S(A|B)_rho` | strongest current working lock |
| primary global kernel | `sum_r w_r I_c(A_r > B_r)_rho` | strongest global/shell form |
| companion diagnostic | `I(A:B)_rho` | useful but secondary |

---

## Bridge `Xi` Options

The unresolved problem is not the existence of the kernel family. It is the bridge into the cut state.

Required shape:

```text
Xi : (geometry sample or history window) -> rho_AB in D(H_A tensor H_B)
```

### Option 1: Pointwise shell-cut bridge

```text
Xi_shell : x -> { (r, w_r, rho_{A_r B_r}(x)) }_r
```

Status:

- strongest source-backed pointwise family
- aligns with the saved shell-cut formula
- still missing an explicit construction rule for `rho_{A_r B_r}(x)`

### Option 2: History-window bridge

```text
Xi_hist : h|_[t0,t1] -> { (t, cut, w_cut, rho_cut(t)) }_{t,cut}
```

Status:

- strongest canon-backed family
- matches the explicit history integral form
- probably the least arbitrary if `Axis 0` is fundamentally trajectory-shaped

### Option 3: Left/right paired bridge

```text
Xi_LR : x -> rho_AB(x) built from paired sheet data
```

Status:

- intuitively tempting
- not source-locked as the final `Axis 0` cut
- currently unsafe to identify with `rho_LR`

### Why `rho_LR` should not be overloaded

In current probe usage, `rho_LR` already means an inter-chirality coherence block inside a larger Weyl-pair construction, not a settled `Axis 0` cut-state symbol.

So the correct statement is:

- `Xi_LR` remains a possible bridge family
- `rho_LR` should not be silently reused as if that were already the finished `Axis 0` object

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

- `torus_transport x Ax0:coarse = 0.7071` on inner and outer torus strata
- `torus_transport x Ax0:coarse = 0.0000` on random `S^3` and Clifford torus samples

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
