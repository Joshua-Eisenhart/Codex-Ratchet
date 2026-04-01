# Axis 0 and Geometric Constraint Manifold

**Date:** 2026-03-29
**Epistemic status:** The direct geometry is source-backed and executable. Axis 0 is source-backed as a continuous cut-state correlation family. The exact bridge `Xi` from geometry/history into a cut state is still open. Runtime `GA0` proxies and symbolic black/white projections are not the same thing as the finished Axis 0 kernel.

---

## Direct Geometry That Is Actually Locked

- [AXIS0_ACTIVE_PACKET_INDEX.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_ACTIVE_PACKET_INDEX.md) is the compact entrypoint for the active `Axis 0` controller, owner, support, and geometry-side packet stack.

| Layer | Pure math | Status |
|---|---|---|
| carrier | `S^3 = {psi in C^2 : ||psi|| = 1}` | source-backed |
| Hopf map | `pi(psi) = psi^dagger sigma_vec psi in S^2` | source-backed |
| torus stratum | `T_eta = {psi(phi, chi; eta) : phi, chi in [0, 2pi)} subset S^3` | source-backed |
| Hopf connection | `A = -i psi^dagger d psi = d phi + cos(2 eta) d chi` | source-backed |
| fiber loop | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | source-backed |
| base loop | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | source-backed |
| horizontal condition | `A(dot gamma_base^s) = 0` | source-backed |
| density reduction | `rho(psi) = |psi><psi| = 1/2 (I + r_vec . sigma_vec)` | source-backed |
| Weyl working layer | `H_L = +H_0`, `H_R = -H_0` | compiled working layer backed by screenshot math |

The geometry is prior to the axes. The axes act on the state/process layer living on that geometry.

---

## Axis 0: What Is Actually Locked

| Layer | Pure math | Status |
|---|---|---|
| canon slice statement | `A_0 : M(C) -> V_0` | locked at role level |
| pointwise pullback shape | `phi_0(x) = Phi_0(rho(x))` | source-backed shape |
| cut-state requirement | `Phi_0` needs `rho_AB in D(H_A tensor H_B)` | locked |
| history-shaped form | `phi_0[h] = (1/T) int_0^T sum_(cut in C) w_cut I_c(cut; rho_h(t)) dt` | user/canon-backed |
| discrete projection | `{Ne, Ni}` vs `{Se, Si}` | projection layer only |

So the live problem is not "what kind of object is Axis 0?" The live problem is:

1. what is the cut `A|B`?
2. what is the bridge `Xi`?
3. is the operative evaluation pointwise, history-shaped, or both?

---

## Strongest Kernel Candidates

| Role | Pure math | Status |
|---|---|---|
| preferred simple kernel | `Phi_0(rho_AB) = -S(A|B)_rho = I_c(A>B)_rho` | strongest current working candidate |
| strongest global shell form | `Phi_0(rho) = sum_r w_r I_c(A_r > B_r)_rho = -sum_r w_r S(A_r|B_r)_rho` | strongest screenshot-backed global form |
| companion diagnostic | `I(A:B)_rho = S(rho_A) + S(rho_B) - S(rho_AB)` | useful, but not signed |
| generic family | `Phi_0(rho_AB)` | source-backed family, not one closed final formula |

Current best read:

- use `-S(A|B)` / coherent information for the simplest signed Axis 0 primitive
- keep weighted shell-cut coherent information as the strongest global form
- keep mutual information as a companion diagnostic, not the kernel by itself

---

## Candidate Bridge Families

| Bridge family | Pure math | Source status | What it buys | What is still wrong/open |
|---|---|---|---|---|
| pointwise shell-cut bridge | `Xi_shell : x -> {(r, w_r, rho_(A_r B_r)(x))}_r` | strongest screenshot-backed pointwise family | lets `phi_0(x)` live directly on the manifold | no concrete construction of `rho_(A_r B_r)(x)` |
| history-window bridge | `Xi_hist : h|_[t0,t1] -> {(t, cut, w_cut, rho_cut(t))}_{t,cut}` | strongest canon-backed family | matches the exact history functional already supplied | still needs a concrete cut family and trajectory-to-state map |
| pointwise abstract bridge | `Xi_pt : x -> (c_x, rho_(c_x)(x))` | abstract source-backed shape | minimal statement of what pointwise Axis 0 would need | too abstract to run |
| coupled L/R bridge | `Xi_LR : x -> rho_LR(x)` | only a tempting candidate, not locked | natural from the Weyl-sheet picture | current repo already uses `rho_LR` as an inter-chirality coherence block; not a safe final Axis 0 bridge |
| torus-latitude bridge | `x -> eta(x)` plus a cut derived from torus shells | geometric candidate only | ties Axis 0 directly to nested Hopf tori | `eta` is a real geometric DOF, but not yet a cut state |
| runtime coarse-graining proxy | engine state -> `GA0` level or coarse/fine knob | runtime-supported proxy only | executable control signal in the engine sims | not the same mathematical object as the cut-state kernel |

---

## What The Sims Actually Support

| Probe | Fresh result | What it actually supports | What it does not prove |
|---|---|---|---|
| `system_v4/probes/axis0_gradient_sim.py` | separable: `I(A:B)=0`, `S(A|B)=1`; Bell: `I(A:B)=2`, `S(A|B)=-1` | the simple signed kernel should be `-S(A|B)` / coherent information | any concrete geometry-to-cut bridge |
| `system_v4/probes/axis0_path_integral_sim.py` | negative conditional entropy, shell-cut coherent info, and coarse-graining monotonicity all pass in one bundle | shell-cut and history-shaped Axis 0 remain live | not a clean final proof of one single Axis 0 formula |
| `system_v4/probes/sim_L0_s3_valid.py` | `S^3`, SU(2), Hopf map, fiber invariance, Berry phase, torus coordinates, and Bloch roundtrip all pass | the direct carrier geometry is real and executable | anything about the cut `A|B` |
| `system_v4/probes/sim_axis_hopf_geometry.py` | torus transport couples to coarse `Axis 0` only on some torus strata | geometry can modulate coarse Axis-0-like behavior | torus transport is not the finished Axis 0 kernel |
| `system_v4/probes/axis0_correlation_sim.py` | builds and burns mutual information, but uses retensorization | older battery proxy is still informative at a rough level | not a defensible finished Axis 0 proof |
| `system_v4/probes/sim_neg_axis0_frozen.py` | freezing runtime Axis 0 degrades the trajectory | the runtime `GA0` control is load-bearing | that runtime `GA0` is already the source-backed cut-state kernel |
| `system_v4/probes/sim_weyl_dof_analysis.py` | Weyl pair analysis reports 8 independent DOF clusters and uses `rho_LR` as an inter-chirality coherence block | the Weyl pair is a rich ambient layer | that `rho_LR` is the final Axis 0 cut state |

---

## Best Current Working Packet

### 1. Geometry

Use the direct carrier geometry:

- `S^3`
- Hopf projection to `S^2`
- nested torus strata `T_eta`
- `gamma_fiber` and `gamma_base`
- density reduction `rho(psi)`

### 2. Axis 0 kernel

Use:

`Phi_0(rho_AB) = -S(A|B)_rho = I_c(A>B)_rho`

as the best simple working kernel.

### 3. Global shell form

Keep:

`Phi_0(rho) = sum_r w_r I_c(A_r > B_r)_rho`

as the strongest global screenshot form.

### 4. Bridge family

Treat:

`Xi_shell` and `Xi_hist`

as the two serious live bridge families.

Current strict cross-lane read:

- strongest live executable bridge family = `Xi_hist`
- strongest exploratory constructive bridge family = cross-temporal chiral (Weyl/chirality-weighted)
- strongest live pointwise discriminator = point-reference
- fixed-marginal preserving lane = certified near-zero on the current carrier

Do not overclose:

- `Xi_LR`
- `eta`-only geometry
- runtime `GA0`

into the final kernel.

---

## Open Gaps

| Gap | Why it matters |
|---|---|
| exact cut `A|B` | without this, `Phi_0` is still only a family |
| explicit `Xi_shell` | needed for a pointwise manifold realization |
| explicit `Xi_hist` | needed for a history-shaped realization |
| earned-vs-constructed bridge closure | strongest exploratory constructive candidate is now identified, but fixed-marginal preserving closure is still near-zero |
| pointwise vs history unification | currently both are live surfaces |
| relation between `Phi_0` and the discrete black/white projection | still not fully closed |
| relation between `eta` and any axis | geometric DOF is real, but not axis-locked |

---

## Best Next Experiments

| Experiment | Input object | Observable | What it would discriminate |
|---|---|---|---|
| `A0-kernel discriminator` | small cut states `rho_AB` | `-S(A|B)`, `I(A:B)`, `sum_r w_r I_c` | strongest primitive entropy family |
| `Hopf pointwise pullback` | geometry samples `x in T_eta` | `phi_0(x)` on fiber vs base loops | whether pointwise Axis 0 is viable |
| `History-vs-pointwise A0` | short channel trajectories `h(t)` | `phi_0(x_t)` vs `phi_0[h]` | whether Axis 0 is static, history-shaped, or both |
| `Xi bridge bakeoff` | same sample under `Xi_shell`, `Xi_hist`, and noncanon `Xi_LR` | sign, monotonicity, loop-family stability | least-arbitrary bridge family |
| `eta-cut test` | fixed torus strata across several `eta` | shell-cut coherent information vs `eta` | whether torus latitude can help define the cut rather than replace it |
