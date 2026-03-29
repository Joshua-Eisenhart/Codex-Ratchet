# Axis 0 Manifold and Bridge Options

**Date:** 2026-03-29  
**Epistemic status:** Working packet. The geometric carrier is strongly source-backed and strongly probe-backed. `Ax0` is source-backed as an external correlation functional on cut states, but the exact bridge from geometry/history into the cut state is still open. This file ranks what is strongest now and what remains candidate-only.

---

## 1. Hard Lock

| Layer | Pure Math | Status |
|---|---|---|
| carrier | \(S^3=\{\psi\in \mathbb C^2:\|\psi\|=1\}\) | source-backed, probe-backed |
| projection | \(\pi(\psi)=\psi^\dagger \vec\sigma\,\psi\in S^2\) | source-backed, probe-backed |
| density reduction | \(\rho(\psi)=|\psi\rangle\langle\psi|=\frac12(I+\vec r\cdot\vec\sigma)\) | source-backed, probe-backed |
| torus stratum | \(T_\eta\subset S^3\) | source-backed, probe-backed |
| loop families | \(\gamma_{\mathrm{fiber}},\gamma_{\mathrm{base}}\subset T_\eta\) | source-backed, probe-backed |
| Weyl sheet layer | \(H_L=+H_0,\ H_R=-H_0\) | source-backed working layer |
| Axis 0 role | \(\varphi_0=\Phi_0\circ \Xi\) | source-backed role, unfinished bridge |
| Axis 0 domain | \(\Phi_0:D(H_A\otimes H_B)\to \mathbb R\) or shell-cut/history generalization | source-backed family |

The main category split is:

- geometry gives the constrained carrier
- `Ax0` does not replace that geometry
- `Ax0` acts on a cut state derived from geometry or history

---

## 2. Best Current Geometry Spine

| Layer | Pure Math | Meaning |
|---|---|---|
| carrier | \(S^3\) | normalized spinor carrier |
| Hopf map | \(\pi:S^3\to S^2\) | Bloch-sphere image |
| torus foliation | \(T_\eta=\{(e^{i\alpha}\cos\eta,\ e^{i\beta}\sin\eta)\}\subset S^3\) | nested Hopf tori |
| connection | \(\mathcal A=-i\psi^\dagger d\psi=d\phi+\cos(2\eta)d\chi\) | separates fiber from horizontal motion |
| fiber loop | \(\gamma_{\mathrm{fiber}}^s(u)=\psi_s(\phi_0+u,\chi_0;\eta_0)\) | density-stationary family |
| base loop | \(\gamma_{\mathrm{base}}^s(u)=\psi_s(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)\) | density-traversing family |
| horizontal condition | \(\mathcal A(\dot\gamma_{\mathrm{base}}^s)=0\) | base-loop constraint |
| sheet sign | \(H_L=+H_0,\ H_R=-H_0\) | coherent orientation flip |

What this does **not** give by itself:

- a bipartite cut state \(\rho_{AB}\)
- a final cut \(A|B\)
- a finished bridge \(\Xi\)

---

## 3. Axis 0 Kernel Candidates

### 3.1 Ranked candidates

| Rank | Pure Math | Role | Status |
|---|---|---|---|
| 1 | \(\Phi_0(\rho_{AB})=-S(A|B)_\rho=I_c(A\rangle B)_\rho\) | strongest simple signed primitive | best current working kernel |
| 2 | \(\Phi_0(\rho)=\sum_r w_r I_c(A_r\rangle B_r)_\rho\) | strongest global shell-cut form | source-backed, bridge still open |
| 3 | \(\Phi_0(\rho_{AB})=I(A:B)_\rho\) | total-correlation diagnostic | useful companion, not enough alone |

### 3.2 Why the ranking looks like this

| Candidate | What it can do | What it cannot do |
|---|---|---|
| \(-S(A|B)\) | goes negative on entangled cuts; gives a signed battery-like primitive | does not choose the cut or bridge by itself |
| \(\sum_r w_r I_c(A_r\rangle B_r)\) | matches the screenshot shell-cut form; scales naturally to manifold/history families | still needs explicit shell construction |
| \(I(A:B)\) | measures total correlation cleanly; useful for diagnostics and monotonicity tests | cannot go negative, so it cannot be the full signed primitive alone |

---

## 4. Axis 0 Shape Family

| Shape | Pure Math | Status |
|---|---|---|
| pointwise manifold pullback | \(\varphi_0(x)=\Phi_0(\rho(x))\) | screenshot-backed shape |
| shell-cut pointwise pullback | \(\varphi_0(x)=\sum_r w_r I_c(A_r\rangle B_r)_{\rho(x)}\) | strongest screenshot-backed pointwise family |
| history functional | \(\varphi_0[h]=\frac1T\int_0^T \sum_{cut\in C} w_{cut} I_c(cut;\rho_h(t))\,dt\) | strongest canon-backed history family |

The unresolved issue is not whether these shapes exist.  
The unresolved issue is how they are unified, if at all.

---

## 5. Bridge Families (Simulated via Exact Liouvillian Integration)

Recent max-real-geometry simulations (`sim_max_real_constraint_manifold.py`) using exact 16-dimensional continuous superoperator integration mathematically prove how each bridge generates correlation, definitively ruling out isolated pointwise tracking. 

### 5.1 The Null Baseline (Why Pointwise Isolated Tracking Fails)

| Evolution | Mathematical Reality | Status |
|---|---|---|
| Uncoupled local evaluation | \(\mathcal{L}_{total} = \mathcal{L}_L \otimes I + I \otimes \mathcal{L}_R \) on product state | Mathematically locked to \(I(L:R) \equiv 0\) permanently. |

To evaluate Axis 0 mathematically, the tracking must move beyond isolated deterministic points.

### 5.2 Viable Correlation-Generating Bridge Options

| Candidate | Pure Math (Simulated Mechanism) | Simulated Result | Status |
|---|---|---|---|
| shell-cut pointwise (\(\Xi_{\mathrm{shell}}\)) | \(x\mapsto \frac{1}{(2\pi)^2}\int\int |\psi_L\rangle\langle\psi_L| \otimes |\psi_R\rangle\langle\psi_R| d\phi d\chi\) | Native \(I(L:R) \sim 0.50\) | **Strongest candidate.** Geometry natively structures spatial envelopes (torus strata) mapping non-local state correlations perfectly matching previous approximations. |
| history-window (\(\Xi_{\mathrm{hist}}\)) | \(h\mapsto \frac{1}{T}\int \rho_{LR}(t) dt\) | Native \(I(L:R) \sim 0.01\) | Strong candidate. Classical trajectory mixing naturally builds global correlation independent of any explicit geometric pairing. |
| constrained coupling (\(\Xi_{\mathrm{coupled}}\)) | \(\mathcal{L}_{total} = \mathcal{L}_{local} - i[H_{int}, \rho]\) | Native \(I(L:R) \sim 0.12\) | Strong candidate. Explicit physics layer enforcing the geometric horizontal constraint \(A(\dot{\gamma}) = 0\). |
| point-reference bridge | \(x\mapsto \{(\mathrm{ref},\rho_{\mathrm{ref}}), (x,\rho(x))\}\) | Evaluates fiber/base distinction but \(I=0\) | Nontrivial scalar diagnostic, but doesn't solve the bipartite correlation requirement. |

### 5.3 What is explicitly not enough

| Object | Problem |
|---|---|
| single isolated spinor \(\psi\) | not bipartite |
| single reduced density \(\rho(\psi)\) | not bipartite |
| raw torus parameter \(\eta\) alone | geometric coordinate, not a cut state |
| mutual information alone | unsigned diagnostic only |
| pointwise decoupled \(\rho_{LR}\) evolution | tensor structure algebraically enforces exactly 0 correlation |

---

## 6. Probe Ranking

### 6.1 Most credible probes

| Rank | Probe | Output | What it actually supports |
|---|---|---|---|
| 1 | [sim_L0_s3_valid.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_L0_s3_valid.py) | [L0_hopf_manifold_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/L0_hopf_manifold_results.json) | the direct carrier geometry is executable: \(S^3\), SU(2), Hopf map, fiber/base behavior, Berry phase, torus coordinates, Bloch round-trip |
| 2 | [axis0_gradient_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_gradient_sim.py) | [axis0_gradient_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_gradient_results.json) | the simple `Ax0` primitive must be able to go negative; \(-S(A|B)\) clears that bar and \(I(A:B)\) does not |
| 3 | [axis0_xi_strict_bakeoff_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_xi_strict_bakeoff_sim.py) | [axis0_xi_strict_bakeoff_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_xi_strict_bakeoff_results.json) | on the live Hopf/Weyl engine, direct `L|R` stays MI-trivial, the shell-strata bridge is pointwise geometry-blind, the point-reference bridge passes the fiber/base discriminator, and the history-window bridge stays nontrivial |
| 4 | [axis0_path_integral_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_path_integral_sim.py) | [axis0_path_integral_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/axis0_path_integral_results.json) | shell-cut and history-shaped `Ax0` remain live possibilities |
| 5 | [sim_neg_axis0_frozen.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_neg_axis0_frozen.py) | [neg_axis0_frozen_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/neg_axis0_frozen_results.json) | current runtime proxy uses something load-bearing called `axis0`, but this does not by itself identify the source-backed kernel |

### 6.2 Useful but lower-authority probes

| Probe | Why it is useful | Why it does not close `Ax0` |
|---|---|---|
| [axis0_correlation_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_correlation_sim.py) | shows MI can be built and burned in a toy coupled system | re-tensorizes states and reports verdicts only on MI |
| [sim_axis_hopf_geometry.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_axis_hopf_geometry.py) | shows some coarse geometric couplings vary by torus stratum | several axis definitions inside the sim are synthetic probes, not source-locked objects |
| [sim_weyl_dof_analysis.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_weyl_dof_analysis.py) | useful warning that the Weyl pair is richer than one torus slice | does not supply a finished `Ax0` cut-state bridge |

---

## 7. What The Current Runs Say

| Claim | Current status |
|---|---|
| the direct manifold \(S^3 \to S^2\) packet is real | supported |
| nested Hopf tori are real carrier structure, not just metaphor | supported |
| `Ax0` needs a signed correlation primitive | supported |
| \(-S(A|B)\) / \(I_c(A\rangle B)\) is the strongest simple kernel | supported |
| shell-cut coherent-information forms remain live | supported, but one naive shell-strata pointwise realization is geometry-blind |
| a pointwise bridge can be made geometry-sensitive on fiber/base loops | supported by the point-reference executable candidate |
| a history-window bridge can be made nontrivial on the live engine without reusing `rho_LR` | supported |
| mutual information is enough by itself | not supported |
| torus transport is the same thing as `Ax0` | not supported |
| the bridge \(\Xi\) is already finished math | not supported |

---

## 8. Fastest Next Experiments

| Experiment | Input object | Observable | What it kills or keeps |
|---|---|---|---|
| kernel discriminator | small cut states \(\rho_{AB}\) | compare \(-S(A|B)\), \(I(A:B)\), and \(\sum_r w_r I_c\) on the same family | strongest entropy primitive |
| pointwise shell discriminator | fixed \(x\in T_\eta\) across fiber/base trajectories | compare shell-strata vs point-reference realizations | kills pointwise bridges that stay constant on both fiber and base |
| history-vs-pointwise test | short stage trajectory \(h(t)\) | compare point-reference \( \varphi_0(x_t)\) and history-window \( \varphi_0[h]\) | whether both shapes are needed |
| bridge bakeoff | same sample under \(\Xi_{\mathrm{shell}}\), point-reference, \(\Xi_{\mathrm{hist}}\), and Weyl-pair toy bridge | sign stability, monotonicity, perturbation sensitivity | least-arbitrary bridge family |

---

## 9. Current Best Read

The cleanest current packet is:

\[
S^3 \to T_\eta \to \gamma_{\mathrm{fiber}},\gamma_{\mathrm{base}} \to \rho(\psi)
\]

for the geometry, and

\[
\Phi_0(\rho_{AB})=-S(A|B)_\rho=I_c(A\rangle B)_\rho
\]

as the best simple `Ax0` kernel, with

\[
\Phi_0(\rho)=\sum_r w_r I_c(A_r\rangle B_r)_\rho
\]

as the strongest global shell-cut form.

The missing object is still:

\[
\Xi:\text{geometry/history} \to \rho_{AB}
\]

plus the exact choice of cut \(A|B\).
