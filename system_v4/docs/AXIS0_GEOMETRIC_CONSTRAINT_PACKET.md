# Axis 0 Geometric Constraint Packet

**Date:** 2026-03-29
**Status:** Working packet. The geometry spine is strong. The simple `Ax0` kernel is strong. The bridge from geometry/history into a cut state is still open.

---

## 1. Direct Geometry Spine

This is the clean geometry that is actually source-backed by the screenshot packet and probe code.

| Layer | Pure math | Status |
|---|---|---|
| carrier | `S^3 = {psi in C^2 : ||psi|| = 1}` | strong |
| Hopf projection | `pi(psi) = psi^dagger sigma_vec psi in S^2` | strong |
| density reduction | `rho(psi) = |psi><psi| = 1/2 (I + r_vec . sigma_vec)` | strong |
| torus stratum | `T_eta subset S^3` | strong |
| fiber loop | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | strong |
| base loop | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | strong |
| Hopf connection | `A = -i psi^dagger d psi = d phi + cos(2 eta) d chi` | strong |
| horizontal condition | `A(dot gamma_base^s) = 0` | strong |
| fiber density path | `rho_f^s(u) = rho_f^s(0)` | strong |
| base density path | `rho_b^s(u) = 1/2 (I + r_vec(chi_0 + u, eta_0) . sigma_vec)` | strong |
| Weyl sheet sign | `H_L = +H_0`, `H_R = -H_0` | working layer, well supported |

The clean stack is:

`S^3 -> T_eta -> {gamma_fiber, gamma_base} -> rho(psi)`

This part is already executable and numerically validated.

---

## 2. What Axis 0 Needs

`Ax0` is not a terrain law and not an operator map. It is an external scalar on a cut state.

The clean shape is:

`phi_0(x) = Phi_0(Xi(x))`

where:

- `x` is a geometry sample or a history sample
- `Xi` is a bridge into a cut state `rho_AB`
- `Phi_0` is a correlation functional on that cut state

So the real unresolved object is:

`Xi : geometry/history -> rho_AB in D(H_A tensor H_B)`

without that bridge, `Ax0` is not finished.

---

## 3. Best Current Kernel Family

These are the live kernel candidates, ranked by current support.

| Role | Pure math | Current status |
|---|---|---|
| strongest simple working kernel | `Phi_0(rho_AB) = -S(A|B)_rho = I_c(A>B)_rho` | strongest |
| strongest global shell form | `Phi_0(rho) = sum_r w_r I_c(A_r > B_r)_rho = - sum_r w_r S(A_r|B_r)_rho` | strongest global form |
| companion diagnostic | `I(A:B)_rho = S(rho_A) + S(rho_B) - S(rho_AB)` | useful, but not enough by itself |

Current practical read:

- if `Ax0` needs a signed battery-like quantity, `-S(A|B)` is the best simple kernel
- if `Ax0` is global over shell cuts, the weighted coherent-information sum is the best source-backed form
- `I(A:B)` is still useful, but as a companion diagnostic rather than the whole kernel

---

## 4. Bridge Families

These are the best current bridge options from geometry/history into a cut state.

| Bridge family | Pure math shape | Status |
|---|---|---|
| pointwise shell-cut bridge | `Xi_shell : x -> {(r, w_r, rho_A_r_B_r(x))}_r` | strongest pointwise candidate |
| history-window bridge | `Xi_hist : h|_[t0,t1] -> {(t, c, w_c, rho_c(t))}_{t,c}` | strongest history candidate |
| pointwise generic cut | `Xi_pt : x -> rho_A_x_B_x(x)` | abstract only |
| left-right paired bridge | `Xi_LR : x -> rho_LR(x)` | possible, but not safe to lock |

Why `Xi_LR` is not locked:

- the screenshot note says a coupled left/right state is one possible input
- local runtime/probe surfaces already use `rho_LR` for a different inter-chirality block meaning
- an uncoupled pair `rho_L tensor rho_R` gives trivial correlation, so it does not solve `Ax0`

So the clean rule is:

- keep `Xi` generic
- prefer shell-cut or history-window bridges
- do not harden `rho_LR` into the canon bridge yet

---

## 5. Simulation-Backed Results

These are the highest-signal local runs.

### 5.1 `axis0_gradient_sim.py`

Fresh result:

- separable state: `I(A:B) = 0`, `S(A|B) = 1`
- Bell state: `I(A:B) = 2`, `S(A|B) = -1`

What it supports:

- `I(A:B)` cannot supply the negative branch by itself
- `-S(A|B)` is the clean simple signed primitive for `Ax0`

Artifacts:

- [/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/axis0_gradient_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_gradient_sim.py)
- [/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/axis0_gradient_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_gradient_results.json)

### 5.2 `axis0_path_integral_sim.py`

Fresh result:

- 2-qubit Bell battery gives negative conditional entropy
- 4-qubit shell cuts give coherent information `1.0000`
- 6-qubit coarse-graining gives `I(A:BC) >= I(A:B)`

What it supports:

- shell-cut and history-like `Ax0` forms stay live
- coarse-graining / shell accumulation is compatible with the weighted coherent-information family

Artifacts:

- [/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/axis0_path_integral_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_path_integral_sim.py)
- [/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/axis0_path_integral_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_path_integral_results.json)

### 5.3 `sim_L0_s3_valid.py`

Fresh result:

- `S^3` validity passes
- `SU(2)` round-trip passes
- Hopf map passes
- fiber preserves base
- fiber closes at `360 deg`
- lifted base loop shows spinor/Berry structure
- torus coordinates and Bloch round-trip pass

What it supports:

- the direct carrier geometry is real and executable
- the Hopf / torus / fiber-base ladder is not just diagram language

Artifacts:

- [/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_L0_s3_valid.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_L0_s3_valid.py)
- [/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/L0_hopf_manifold_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/L0_hopf_manifold_results.json)

### 5.4 `sim_axis_hopf_geometry.py`

Fresh result:

- `torus_transport x Ax0:coarse = 0.7071` on inner and outer torus strata
- `torus_transport x Ax0:coarse = 0.0000` on random `S^3`, Clifford torus, and mixed states
- `fiber_phase x Ax3:chirality = 0.0000`

What it supports:

- torus transport can couple to a coarse `Ax0` proxy on some torus strata
- torus transport is not the universal `Ax0` kernel
- coarse-graining proxies and direct geometry are not identical objects

Artifacts:

- [/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis_hopf_geometry.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_axis_hopf_geometry.py)
- [/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/sim_results/axis_hopf_geometry_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/sim_results/axis_hopf_geometry_results.json)

### 5.5 `axis0_correlation_sim.py`

Fresh result:

- mutual information is built up, then burned back to zero
- conditional entropy never becomes negative in that script

What it supports:

- mutual information works as a runtime battery proxy
- this is not strong enough to replace the signed cut-state kernel
- the script uses retensorization, so it should stay demoted

Artifacts:

- [/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/axis0_correlation_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_correlation_sim.py)
- [/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/axis0_correlation_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_correlation_results.json)

### 5.6 `sim_neg_axis0_frozen.py`

Fresh result:

- frozen `axis0 = 0.1`
- `D(adapt, frozen)_L = 0.1466`
- `D(adapt, frozen)_R = 0.0604`
- `ga0_adapt / ga0_frozen = 0.471 / 0.100`
- `5/6` axes differ

What it supports:

- the current runtime `ga0` control is load-bearing
- this still does not prove that the runtime control variable is the same object as the clean cut-state `Ax0` kernel

Artifacts:

- [/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_neg_axis0_frozen.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_neg_axis0_frozen.py)
- [/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/neg_axis0_frozen_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/neg_axis0_frozen_results.json)

---

## 6. Best Current Working Lock

| Piece | Best current read |
|---|---|
| direct manifold | `S^3 -> T_eta -> gamma_fiber / gamma_base -> rho(psi)` |
| simple `Ax0` kernel | `Phi_0(rho_AB) = -S(A|B)_rho = I_c(A>B)_rho` |
| strongest global `Ax0` form | `sum_r w_r I_c(A_r > B_r)_rho` |
| strongest bridge family | shell-cut or history-window |
| safest status for `rho_LR` bridge | possible but not locked |
| runtime `ga0` variable | load-bearing proxy, not yet the finished `Ax0` kernel |

---

## 7. What Is Still Missing

`Ax0` is still unfinished because these pieces are not closed:

1. the exact cut family `A|B`
2. the exact bridge `Xi`
3. the exact relation between pointwise `phi_0(x)` and history-shaped `phi_0[h]`
4. the exact relation between the clean cut-state kernel and the runtime `ga0` control proxy

So the honest status is:

- geometry spine: strong
- simple `Ax0` kernel: strong
- shell-cut global form: strong
- bridge from geometry/history into `rho_AB`: still open

---

## 8. Highest-Signal Next Sims

| Sim | Input object | Observable | What it would discriminate |
|---|---|---|---|
| kernel discriminator | fixed small `rho_AB` families | `-S(A|B)`, `I(A:B)`, `sum_r w_r I_c` | which kernel should be primary vs companion |
| pointwise shell-cut pullback | fixed torus samples on one `T_eta` | constancy on fiber, variation on base | whether `phi_0(x)` is meaningful as a pointwise manifold field |
| history vs pointwise | one short trajectory with a fixed cut family | `phi_0(x_t)` vs `phi_0[h]` | whether `Ax0` is fundamentally pointwise, history-shaped, or both |
| bridge bakeoff | same sample under shell-cut, history-window, and tentative L/R pair bridges | sign, stability, perturbation sensitivity | least-arbitrary `Xi` family |
| runtime bridge test | current `ga0` runtime surface and a clean shell-cut evaluation on the same run | correlation and lag | whether runtime `ga0` is a proxy for the clean `Ax0` kernel or a different control variable |
