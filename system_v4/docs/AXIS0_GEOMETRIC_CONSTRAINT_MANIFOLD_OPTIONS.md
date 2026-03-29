# Axis 0 and Geometric Constraint Manifold

**Date:** 2026-03-29
**Epistemic status:** Working packet. The direct geometry is source-backed and probe-backed. The Axis 0 kernel family is source-backed. The exact bridge from geometry or history into a cut state is still open.

---

## Scope

This packet isolates only:

1. the geometric constraint manifold
2. the live Axis 0 kernel family
3. the bridge problem `Xi : geometry/history -> rho_AB`
4. the cut problem `A|B`
5. what current sims do and do not support

It does not try to settle Ax3-Ax6.

---

## Direct Geometry Spine

### Canon statement

| Layer | Pure Math | Status |
|---|---|---|
| constraint manifold | `M(C) = {x : x is admissible under C}` | source-backed |
| Axis 0 slice | `A0 : M(C) -> V0` | source-backed |

### Concrete realization used by the current packet

| Layer | Pure Math | Status |
|---|---|---|
| carrier | `S^3 = {psi in C^2 : ||psi|| = 1}` | source-backed and probe-backed |
| Hopf projection | `pi(psi) = psi^dagger sigma_vec psi in S^2` | source-backed and probe-backed |
| torus stratum | `T_eta = {(e^(i alpha) cos eta, e^(i beta) sin eta) : alpha,beta in S^1} subset S^3` | source-backed and probe-backed |
| Hopf connection | `A = -i psi^dagger d psi = d phi + cos(2 eta) d chi` | source-backed |
| fiber loop | `gamma_fiber^s(u) = psi_s(phi0 + u, chi0; eta0)` | source-backed and probe-backed |
| base loop | `gamma_base^s(u) = psi_s(phi0 - cos(2 eta0) u, chi0 + u; eta0)` | source-backed and probe-backed |
| horizontal condition | `A(dot gamma_base^s) = 0` | source-backed |
| fiber density path | `rho_f^s(u) = |gamma_f^s(u)><gamma_f^s(u)| = rho_f^s(0)` | source-backed |
| base density path | `rho_b^s(u) = |gamma_b^s(u)><gamma_b^s(u)| = 1/2 (I + r_vec(chi0 + u, eta0) . sigma_vec)` | source-backed |
| density reduction | `rho(psi) = |psi><psi| = 1/2 (I + r_vec . sigma_vec)` | source-backed and probe-backed |

### Compiled working layer above the direct geometry

| Layer | Pure Math | Status |
|---|---|---|
| Weyl sheets | `H_L = +H0`, `H_R = -H0` | source-backed working layer |
| terrain sheet variable | `s in {L,R}` | compiled working layer |
| terrain laws | `X_{tau,s}` | compiled working layer |
| operator layer | `J_o` | compiled working layer |
| precedence layer | `Psi^up`, `Psi^down` | compiled working layer |

Important separation:

- `fiber/base` is direct geometry
- `inner/outer` is later naming and may be engine-indexed
- `L/R` Weyl sheets are a working layer on top of the carrier geometry

---

## What Axis 0 Is Allowed To Act On

Source packet:

`varphi_0(x) = Phi_0(rho(x))`

with the explicit caveat that a single isolated Weyl spinor is not enough for conditional entropy.

So the minimum honest statement is:

| Object | Pure Math | Status |
|---|---|---|
| pointwise manifold form | `varphi_0(x) = Phi_0(rho(x))` | source-backed shape |
| required state type | `rho_AB in D(H_A tensor H_B)` | source-backed |
| bridge placeholder | `Xi : (geometry sample or history window) -> rho_AB` | compiled placeholder only |

This means Axis 0 acts on the manifold only after a bridge has attached a cut state to the geometry or to a history window.

---

## Axis 0 Kernel Family

### Source-backed family

| Role | Pure Math | Status |
|---|---|---|
| generic kernel family | `Phi_0(rho_AB)` | source-backed family only |
| shell-cut form | `Phi_0(rho) = sum_r w_r I_c(A_r > B_r)_rho = - sum_r w_r S(A_r|B_r)_rho` | strongest screenshot-backed global form |
| simple bipartite form | `Phi_0(rho_AB) = -S(A|B)_rho = I_c(A > B)_rho` | strongest simple working candidate |
| companion diagnostic | `I(A:B)_rho = S(rho_A) + S(rho_B) - S(rho_AB)` | source-backed companion |
| history form | `varphi_0[h] = (1/T) integral_0^T sum_{cut in C} w_cut I_c(cut; rho_h(t)) dt` | canon-backed history form |

### Current ranking

| Candidate | Pure Math | Why it stays live | Current standing |
|---|---|---|---|
| coherent-information primitive | `-S(A|B)_rho = I_c(A > B)_rho` | only simple candidate that can be negative | strongest simple kernel |
| shell-cut coherent family | `sum_r w_r I_c(A_r > B_r)_rho` | directly matches the screenshot packet | strongest global form |
| mutual information | `I(A:B)_rho` | tracks total correlation and coarse-graining growth | companion diagnostic, not enough by itself for the signed battery role |

### Proposal-only competitors from the brain lane

These remain proposal surfaces, not source-locked kernel math:

| Proposal | Pure Math | Status |
|---|---|---|
| correlation-spread diversity | `D(lambda) = exp(H(lambda))` built from normalized pairwise mutual informations | proposal only |
| variance damping | `Var(lambda)` over pairwise mutual informations | proposal only |
| total-correlation response | `T(rho) = sum_i S(rho_i) - S(rho)` with response derivative | proposal only |
| path entropy | `H_path = - sum_{k_vec} P(k_vec) log P(k_vec)` | proposal only |

These are useful search surfaces, but they are not the strongest current lock.

---

## What The Current Sims Support

| Probe | Result | What it supports | What it does not support |
|---|---|---|---|
| `system_v4/probes/axis0_gradient_sim.py` | separable: `I=0`, `S(A|B)=1`; Bell: `I=2`, `S(A|B)=-1` | `-S(A|B)` is the strongest simple signed kernel | does not choose the cut or the bridge |
| `system_v4/probes/axis0_path_integral_sim.py` | negative conditional entropy, coherent-information shell cuts, and MI monotonicity all appear in one bundle | shell-cut and history-shaped Ax0 remain live | mixes several proxies, so it does not settle one final bridge |
| `system_v4/probes/axis0_xi_strict_bakeoff_sim.py` | direct `L|R` stays MI-trivial on the live engine, shell-strata pointwise is geometry-blind, point-reference varies on base while staying constant on fiber, and history-window stays nontrivial | the bridge problem can now be tested on the live Hopf/Weyl engine without superposition shortcuts | still does not settle one final doctrine-level bridge |
| `system_v4/probes/sim_L0_s3_valid.py` | `S^3`, SU(2), Hopf map, fiber/base behavior, Berry phase, torus coordinates all validate | the direct geometry spine is executable | says nothing by itself about the cut state |
| `system_v4/probes/sim_axis_hopf_geometry.py` | torus transport overlaps with coarse Ax0 on some torus strata, but not universally | torus transport can affect coarse Ax0-like proxies in specific strata | torus transport is not the full Ax0 kernel |
| `system_v4/probes/sim_weyl_dof_analysis.py` | Weyl-pair layer has 8 independent DOF clusters and treats `rho_LR` as an inter-chirality coherence block | the Weyl pair is richer than one torus slice | warns against casually reusing `rho_LR` as the Ax0 cut-state symbol |
| `results_axis0_traj_corr_suite.json` | tracks trajectory means of `I(A:B)` and `S(A|B)` across cycle families | history-window Ax0 is plausible | still not a clean source-backed bridge from geometry into a chosen cut |

Operational read:

- the geometry layer is real
- the signed Ax0 primitive is real
- the bridge is the missing object

---

## Bridge Families

### Source-backed families

| Bridge family | Pure Math | Strength | Main gap |
|---|---|---|---|
| generic pointwise bridge | `Xi_pt : x -> (c_x, rho_{c_x}(x))` | matches `varphi_0(x) = Phi_0(rho(x))` | the cut `c_x = A_x|B_x` is not fixed |
| shell-cut bridge | `Xi_shell : x -> {(r, w_r, rho_{A_r B_r}(x))}_r` | strongest screenshot-backed bridge family | needs a concrete shell algebra or shell partition |
| history-window bridge | `Xi_hist : h|_[t0,t1] -> {(t, c, w_c, rho_c(t))}_{t,c}` | strongest match to the canon history functional | needs a concrete trajectory-to-cut construction |

### Candidate but not yet safe to promote

| Candidate | Pure Math | Why it is tempting | Why it is not locked |
|---|---|---|---|
| left/right sheet cut | `rho_{LR}(x)` | directly available from the Weyl working layer | `rho_LR` already has another repo meaning; the uncoupled product version is trivial for Ax0 |
| fiber/base cut | `rho_{fiber,base}(x)` | directly tied to loop geometry | not source-backed as the Ax0 cut |
| torus-latitude cut | a cut induced by `eta` or inner/outer shell latitude | directly geometric | still only a proposal |
| fixed-reference pointwise bridge | `x -> {(ref, rho_ref), (x, rho(x))}` | passes the fiber/base discriminator on the live engine geometry | compiled executable candidate, not source-locked doctrine |

### Important inference

If one uses an uncoupled pure product state

`rho_AB = rho_L tensor rho_R`

then standard QIT gives

`I(A:B) = 0`

and

`-S(A|B) = 0`

for pure single-qubit factors.

So a useful Ax0 bridge cannot just be "take two independent pure sheet states and tensor them together." It needs a genuinely coupled cut state or a nontrivial reduced multipartite state.

---

## Candidate Cuts

| Cut | Pure Math | Strength | Risk |
|---|---|---|---|
| shell boundary/interior | `I_r | B_r` | strongest screenshot-style cut | exact shell algebra not written |
| generic bipartite cut | `A|B` | minimal QIT requirement | too abstract by itself |
| history cut family | `cut in C` along `rho_h(t)` | strongest canon history form | needs a concrete trajectory state construction |
| left/right sheet cut | `L|R` | geometrically available | currently overloaded and not source-locked as Ax0 doctrine |

Best current read:

- shell boundary/interior is the strongest geometric-QIT cut family
- generic `A|B` is the safest abstract notation
- `L|R` stays only as a candidate, not the lock

---

## Finished vs Unfinished

| Item | Status |
|---|---|
| `S^3 -> Hopf -> T_eta -> fiber/base -> rho(psi)` geometry spine | finished enough for working use |
| Axis 0 as an external cut-state correlation family | finished enough for working use |
| `-S(A|B)` as strongest simple kernel | finished enough for working use |
| shell-cut coherent-information family | finished enough for working use |
| exact cut `A|B` | unfinished |
| exact bridge `Xi` | unfinished |
| pointwise vs history unification | unfinished |
| discrete projection rule from continuous `Phi_0` to a local sign or class | unfinished |
| any claim that torus transport by itself is Ax0 | not supported |

---

## Fastest Next Discriminators

| Sim | Input | Compare | Kill criterion |
|---|---|---|---|
| bridge bakeoff | same geometry sample under `Xi_pt`, `Xi_shell`, `Xi_hist` | sign stability, perturbation response, loop-family behavior | any bridge with unstable sign under tiny geometric perturbation dies first |
| pointwise fiber/base Ax0 | fixed `T_eta` with fiber and base paths | compare shell-strata and fixed-reference realizations of `varphi_0(gamma_fiber(u))` vs `varphi_0(gamma_base(u))` | if both are constant under a reasonable bridge, the bridge is probably empty |
| history vs pointwise Ax0 | same trajectory sampled both pointwise and as a history window | `varphi_0(x_t)` vs `varphi_0[h]` | if one collapses to noise while the other carries signal, they are not the same object |
| shell-cut geometry probe | explicit shell/interior construction on nested torus samples | `sum_r w_r I_c(A_r > B_r)` | if no nontrivial cut state can be attached, shell-cut remains only a slogan |

---

## Current Working Lock

The best current working position is:

1. the geometric constraint manifold is real and already executable at the `S^3 / Hopf / T_eta / fiber-base / rho(psi)` level
2. Axis 0 is a primitive continuous correlation functional on cut states attached to that geometry or to its histories
3. the strongest simple working kernel is

`Phi_0(rho_AB) = -S(A|B)_rho = I_c(A > B)_rho`

4. the strongest global screenshot form is

`Phi_0(rho) = sum_r w_r I_c(A_r > B_r)_rho`

5. the unresolved core is not the kernel family anymore; it is the bridge

`Xi : geometry/history -> rho_AB`

and the cut

`A|B`
