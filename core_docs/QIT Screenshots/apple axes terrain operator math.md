


￼

￼



## Inward / Type 1 Terrains

| Type | Terrain | Code | Equation |
|---|---|---|---|
| Type 1 | Funnel | `Se-IN` | \(\dot\rho=\sum_k D_{L^{Se,\mathrm{in}}_k}(\rho)-i\,\varepsilon_{Se,\mathrm{in}}[H_0,\rho]\) |
| Type 1 | Vortex | `Ne-IN` | \(\dot\rho=-i[H_0,\rho]+\varepsilon_{Ne,\mathrm{in}}\sum_k D_{L^{Ne,\mathrm{in}}_k}(\rho)\) |
| Type 1 | Pit | `Ni-IN` | \(\dot\rho=D_{L^{Ni,\mathrm{in}}}(\rho)-i\,\varepsilon_{Ni,\mathrm{in}}[H_0,\rho]\) |
| Type 1 | Hill | `Si-IN` | \(\dot\rho=-i[H_C^{\mathrm{in}},\rho]+\sum_j \kappa_j^{\mathrm{in}}\left(P_j^{\mathrm{in}}\rho P_j^{\mathrm{in}}-\frac12(P_j^{\mathrm{in}}\rho+\rho P_j^{\mathrm{in}})\right)\), with \([H_C^{\mathrm{in}},P_j^{\mathrm{in}}]=0\) |

## Outward / Type 2 Terrains

| Type | Terrain | Code | Equation |
|---|---|---|---|
| Type 2 | Cannon | `Se-OUT` | \(\dot\rho=\sum_k D_{L^{Se,\mathrm{out}}_k}(\rho)+i\,\varepsilon_{Se,\mathrm{out}}[H_0,\rho]\) |
| Type 2 | Spiral | `Ne-OUT` | \(\dot\rho=+i[H_0,\rho]+\varepsilon_{Ne,\mathrm{out}}\sum_k D_{L^{Ne,\mathrm{out}}_k}(\rho)\) |
| Type 2 | Source | `Ni-OUT` | \(\dot\rho=D_{L^{Ni,\mathrm{out}}}(\rho)+i\,\varepsilon_{Ni,\mathrm{out}}[H_0,\rho]\) |
| Type 2 | Citadel | `Si-OUT` | \(\dot\rho=+i[H_C^{\mathrm{out}},\rho]+\sum_j \kappa_j^{\mathrm{out}}\left(P_j^{\mathrm{out}}\rho P_j^{\mathrm{out}}-\frac12(P_j^{\mathrm{out}}\rho+\rho P_j^{\mathrm{out}})\right)\), with \([H_C^{\mathrm{out}},P_j^{\mathrm{out}}]=0\) |

## Shared Definitions

\[
H_0 = n_x\sigma_x + n_y\sigma_y + n_z\sigma_z
\]

\[
D_L(\rho)=L\rho L^\dagger-\frac12\left(L^\dagger L\rho+\rho L^\dagger L\right)
\]

## Pairing Table

| Family | Type 1 | Type 2 |
|---|---|---|
| `Se` | Funnel | Cannon |
| `Ne` | Vortex | Spiral |
| `Ni` | Pit | Source |
| `Si` | Hill | Citadel |

So yes:
- `Type 1 = inward`
- `Type 2 = outward`

and the jargon labels can sit on the table without entering the equations.       ———   Use this manifold embedding.

## Carrier

\[
S^3=\{\psi\in \mathbb C^2:\|\psi\|=1\}
\]

\[
\pi(\psi)=\psi^\dagger \vec\sigma\,\psi\in S^2
\]

\[
\rho(\psi)=|\psi\rangle\langle\psi|
=\frac12\left(I+\vec r\cdot \vec\sigma\right)
\]

\[
\vec\sigma=(\sigma_x,\sigma_y,\sigma_z)
\]

A nested Hopf-torus family can be written as

\[
T_\eta=\{(e^{i\alpha}\cos\eta,\ e^{i\beta}\sin\eta):\alpha,\beta\in S^1\}\subset S^3
\]

with:
- inner loop = Hopf fiber loop
- outer loop = lifted base loop

## Weyl sectors

Use the two Weyl sectors as the two global orientation sheets:

\[
\rho_L=\frac12(I+\vec r_L\cdot\vec\sigma),\qquad
\rho_R=\frac12(I+\vec r_R\cdot\vec\sigma)
\]

\[
H_0=n_x\sigma_x+n_y\sigma_y+n_z\sigma_z
\]

\[
H_L=+H_0,\qquad H_R=-H_0
\]

So the Hamiltonian circulation is

\[
\dot\rho_L=-i[H_L,\rho_L],\qquad
\dot\rho_R=-i[H_R,\rho_R]
\]

or in Bloch-vector form

\[
\dot{\vec r}_L=2\,\vec n\times \vec r_L,\qquad
\dot{\vec r}_R=-2\,\vec n\times \vec r_R
\]

That is the clean Pauli/Weyl sign flip.

## Type 1 / Inward on Left-Weyl Sheet

| Terrain | Exact law on spinor density matrix | Pauli realization | Hopf-torus action |
|---|---|---|---|
| Funnel | \(\dot\rho_L=\sum_k D_{L^{Se,\mathrm{in}}_k}(\rho_L)-i\,\varepsilon_{Se,\mathrm{in}}[H_L,\rho_L]\) | \(L^{Se,\mathrm{in}}_k=a^{Se,\mathrm{in}}_{k0}I+\vec a^{Se,\mathrm{in}}_k\cdot\vec\sigma\) | support transport across nested tori with inward-oriented sheet |
| Vortex | \(\dot\rho_L=-i[H_L,\rho_L]+\varepsilon_{Ne,\mathrm{in}}\sum_k D_{L^{Ne,\mathrm{in}}_k}(\rho_L)\) | \(H_L=+\,\vec n\cdot\vec\sigma\) | tangential circulation on a fixed Hopf torus; inner=fiber, outer=horizontal lift |
| Pit | \(\dot\rho_L=D_{L^{Ni,\mathrm{in}}}(\rho_L)-i\,\varepsilon_{Ni,\mathrm{in}}[H_L,\rho_L]\) | minimal choice \(L^{Ni,\mathrm{in}}=\sqrt{\gamma}\,\sigma_-\) | contraction from larger torus shells toward inner/core attractor |
| Hill | \(\dot\rho_L=-i[H_S^{\mathrm{in}},\rho_L]+\sum_j\kappa_j^{\mathrm{in}}\left(P_j^{\mathrm{in}}\rho_LP_j^{\mathrm{in}}-\frac12(P_j^{\mathrm{in}}\rho_L+\rho_LP_j^{\mathrm{in}})\right)\) | \(P_j^{\mathrm{in}}=\frac12(I+\hat m_j^{\mathrm{in}}\cdot\vec\sigma)\), \([H_S^{\mathrm{in}},P_j^{\mathrm{in}}]=0\) | confinement on invariant torus strata / retained terraces |

## Type 2 / Outward on Right-Weyl Sheet

| Terrain | Exact law on spinor density matrix | Pauli realization | Hopf-torus action |
|---|---|---|---|
| Cannon | \(\dot\rho_R=\sum_k D_{L^{Se,\mathrm{out}}_k}(\rho_R)-i\,\varepsilon_{Se,\mathrm{out}}[H_R,\rho_R]\) | \(L^{Se,\mathrm{out}}_k=a^{Se,\mathrm{out}}_{k0}I+\vec a^{Se,\mathrm{out}}_k\cdot\vec\sigma\) | support transport across nested tori with outward-oriented sheet |
| Spiral | \(\dot\rho_R=-i[H_R,\rho_R]+\varepsilon_{Ne,\mathrm{out}}\sum_k D_{L^{Ne,\mathrm{out}}_k}(\rho_R)\) | \(H_R=-\,\vec n\cdot\vec\sigma\) | opposite tangential circulation on a fixed Hopf torus |
| Source | \(\dot\rho_R=D_{L^{Ni,\mathrm{out}}}(\rho_R)-i\,\varepsilon_{Ni,\mathrm{out}}[H_R,\rho_R]\) | minimal choice \(L^{Ni,\mathrm{out}}=\sqrt{\gamma}\,\sigma_+\) | emission from inner/core torus region toward outer shells |
| Citadel | \(\dot\rho_R=-i[H_S^{\mathrm{out}},\rho_R]+\sum_j\kappa_j^{\mathrm{out}}\left(P_j^{\mathrm{out}}\rho_RP_j^{\mathrm{out}}-\frac12(P_j^{\mathrm{out}}\rho_R+\rho_RP_j^{\mathrm{out}})\right)\) | \(P_j^{\mathrm{out}}=\frac12(I+\hat m_j^{\mathrm{out}}\cdot\vec\sigma)\), \([H_S^{\mathrm{out}},P_j^{\mathrm{out}}]=0\) | retained outward strata with opposite global orientation |

## Exact pair lock

| Pair | Left-Weyl / Type 1 | Right-Weyl / Type 2 | actual difference |
|---|---|---|---|
| Funnel / Cannon | \(H_L=+H_0,\ L_k^{Se,\mathrm{in}}\) | \(H_R=-H_0,\ L_k^{Se,\mathrm{out}}\) | opposite Weyl orientation and distinct Lindblad family |
| Vortex / Spiral | \(+H_0\) circulation | \(-H_0\) circulation | opposite Hopf circulation handedness |
| Pit / Source | \(L=\sqrt{\gamma}\sigma_-\) | \(L=\sqrt{\gamma}\sigma_+\) | sink vs source in Pauli ladder operators |
| Hill / Citadel | \(H_S^{\mathrm{in}},P_j^{\mathrm{in}}\) | \(H_S^{\mathrm{out}},P_j^{\mathrm{out}}\) | distinct retained strata on opposite orientation sheets |

## Loop placement

Each of these 8 terrain laws exists on both loop families:

\[
\Gamma_{\mathrm{inner}}:\text{Hopf fiber loop},\qquad
\Gamma_{\mathrm{outer}}:\text{lifted base loop}
\]

The terrain law does not change family when moved between inner and outer loop. What changes is whether the induced vector field is resolved along:
- fiber direction
- horizontal lifted-base direction

So the clean stack is:

\[
\text{Pauli matrices} \to \text{Weyl spinor densities} \to \text{terrain law} \to \text{inner/outer Hopf-torus loop placement}
\]

That is the direct mapping.

￼
   **Carrier**

| Object | Formula | Meaning |
|---|---|---|
| spinor carrier | \(\psi\in\mathbb C^2,\ \|\psi\|=1\) | normalized 2-spinor |
| pure-state manifold | \(S^3=\{\psi\in\mathbb C^2:\|\psi\|=1\}\) | carrier space |
| Hopf projection | \(\pi(\psi)=\psi^\dagger \vec\sigma\,\psi\in S^2\) | Bloch-sphere projection |
| density matrix | \(\rho(\psi)=|\psi\rangle\langle\psi|=\frac12(I+\vec r\cdot\vec\sigma)\) | state in Pauli form |
| Pauli basis | \(\vec\sigma=(\sigma_x,\sigma_y,\sigma_z)\) | local operator basis |

**Pauli Matrices**

| Symbol | Matrix |
|---|---|
| \(I\) | \(\begin{pmatrix}1&0\\0&1\end{pmatrix}\) |
| \(\sigma_x\) | \(\begin{pmatrix}0&1\\1&0\end{pmatrix}\) |
| \(\sigma_y\) | \(\begin{pmatrix}0&-i\\ i&0\end{pmatrix}\) |
| \(\sigma_z\) | \(\begin{pmatrix}1&0\\0&-1\end{pmatrix}\) |
| \(\sigma_-\) | \(\begin{pmatrix}0&0\\1&0\end{pmatrix}\) |
| \(\sigma_+\) | \(\begin{pmatrix}0&1\\0&0\end{pmatrix}\) |

**Nested Hopf Tori**

| Object | Formula | Meaning |
|---|---|---|
| torus family | \(T_\eta=\{(e^{i\alpha}\cos\eta,\ e^{i\beta}\sin\eta):\alpha,\beta\in S^1\}\subset S^3\) | nested Hopf-torus family |
| inner loop | \(\Gamma_{\mathrm{inner}}\) | Hopf fiber loop |
| outer loop | \(\Gamma_{\mathrm{outer}}\) | lifted base loop |

**Weyl Sheets**

| Engine type | Sheet | Density | Hamiltonian |
|---|---|---|---|
| Type 1 | left Weyl | \(\rho_L=\frac12(I+\vec r_L\cdot\vec\sigma)\) | \(H_L=+H_0\) |
| Type 2 | right Weyl | \(\rho_R=\frac12(I+\vec r_R\cdot\vec\sigma)\) | \(H_R=-H_0\) |

| Shared object | Formula |
|---|---|
| base Hamiltonian | \(H_0=n_x\sigma_x+n_y\sigma_y+n_z\sigma_z\) |

**Weyl Rotation Laws**

| Engine type | Density law | Bloch-vector law |
|---|---|---|
| Type 1 | \(\dot\rho_L=-i[H_L,\rho_L]\) | \(\dot{\vec r}_L=2\,\vec n\times \vec r_L\) |
| Type 2 | \(\dot\rho_R=-i[H_R,\rho_R]\) | \(\dot{\vec r}_R=-2\,\vec n\times \vec r_R\) |

**Dissipator**

| Object | Formula |
|---|---|
| Lindblad dissipator | \(D[L](\rho)=L\rho L^\dagger-\frac12(L^\dagger L\rho+\rho L^\dagger L)\) |

**Type 1 Terrain Laws**

| Terrain | Topology family | Law on \(\rho_L\) | Pauli realization | Geometric read |
|---|---|---|---|---|
| Funnel | `Se` | \(\dot\rho_L=\sum_k D[L_k^{Se,\mathrm{in}}](\rho_L)-i\,\varepsilon_{Se,\mathrm{in}}[H_L,\rho_L]\) | \(L_k^{Se,\mathrm{in}}=a_{k0}^{Se,\mathrm{in}}I+\vec a_k^{Se,\mathrm{in}}\cdot\vec\sigma\) | inward support transport across nested tori |
| Vortex | `Ne` | \(\dot\rho_L=-i[H_L,\rho_L]+\varepsilon_{Ne,\mathrm{in}}\sum_k D[L_k^{Ne,\mathrm{in}}](\rho_L)\) | Hamiltonian-led circulation with \(H_L=+\vec n\cdot\vec\sigma\) | left-handed tangential circulation on fixed Hopf torus |
| Pit | `Ni` | \(\dot\rho_L=D[L^{Ni,\mathrm{in}}](\rho_L)-i\,\varepsilon_{Ni,\mathrm{in}}[H_L,\rho_L]\) | \(L^{Ni,\mathrm{in}}=\sqrt\gamma\,\sigma_-\) | contraction from larger torus shells toward inner/core attractor |
| Hill | `Si` | \(\dot\rho_L=-i[H_S^{\mathrm{in}},\rho_L]+\sum_j\kappa_j^{\mathrm{in}}\left(P_j^{\mathrm{in}}\rho_LP_j^{\mathrm{in}}-\frac12(P_j^{\mathrm{in}}\rho_L+\rho_LP_j^{\mathrm{in}})\right)\) | \(P_j^{\mathrm{in}}=\frac12(I+\hat m_j^{\mathrm{in}}\cdot\vec\sigma)\), \([H_S^{\mathrm{in}},P_j^{\mathrm{in}}]=0\) | retained invariant terraces |

**Type 2 Terrain Laws**

| Terrain | Topology family | Law on \(\rho_R\) | Pauli realization | Geometric read |
|---|---|---|---|---|
| Cannon | `Se` | \(\dot\rho_R=\sum_k D[L_k^{Se,\mathrm{out}}](\rho_R)-i\,\varepsilon_{Se,\mathrm{out}}[H_R,\rho_R]\) | \(L_k^{Se,\mathrm{out}}=a_{k0}^{Se,\mathrm{out}}I+\vec a_k^{Se,\mathrm{out}}\cdot\vec\sigma\) | outward support transport across nested tori |
| Spiral | `Ne` | \(\dot\rho_R=-i[H_R,\rho_R]+\varepsilon_{Ne,\mathrm{out}}\sum_k D[L_k^{Ne,\mathrm{out}}](\rho_R)\) | Hamiltonian-led circulation with \(H_R=-\vec n\cdot\vec\sigma\) | right-handed tangential circulation on fixed Hopf torus |
| Source | `Ni` | \(\dot\rho_R=D[L^{Ni,\mathrm{out}}](\rho_R)-i\,\varepsilon_{Ni,\mathrm{out}}[H_R,\rho_R]\) | \(L^{Ni,\mathrm{out}}=\sqrt\gamma\,\sigma_+\) | emission from inner/core torus region toward outer shells |
| Citadel | `Si` | \(\dot\rho_R=-i[H_S^{\mathrm{out}},\rho_R]+\sum_j\kappa_j^{\mathrm{out}}\left(P_j^{\mathrm{out}}\rho_RP_j^{\mathrm{out}}-\frac12(P_j^{\mathrm{out}}\rho_R+\rho_RP_j^{\mathrm{out}})\right)\) | \(P_j^{\mathrm{out}}=\frac12(I+\hat m_j^{\mathrm{out}}\cdot\vec\sigma)\), \([H_S^{\mathrm{out}},P_j^{\mathrm{out}}]=0\) | retained outward strata on opposite sheet |

**Exact Terrain Pair Separation**

| Pair | Type 1 law | Type 2 law | Actual mathematical difference |
|---|---|---|---|
| Funnel / Cannon | \(\sum_k D[L_k^{Se,\mathrm{in}}](\rho_L)-i\,\varepsilon_{Se,\mathrm{in}}[H_L,\rho_L]\) | \(\sum_k D[L_k^{Se,\mathrm{out}}](\rho_R)-i\,\varepsilon_{Se,\mathrm{out}}[H_R,\rho_R]\) | opposite Weyl sign and distinct dissipative family |
| Vortex / Spiral | \(-i[H_L,\rho_L]+\varepsilon_{Ne,\mathrm{in}}\sum_k D[L_k^{Ne,\mathrm{in}}](\rho_L)\) | \(-i[H_R,\rho_R]+\varepsilon_{Ne,\mathrm{out}}\sum_k D[L_k^{Ne,\mathrm{out}}](\rho_R)\) | opposite Hopf circulation handedness |
| Pit / Source | \(D[\sqrt\gamma\,\sigma_-](\rho_L)-i\,\varepsilon_{Ni,\mathrm{in}}[H_L,\rho_L]\) | \(D[\sqrt\gamma\,\sigma_+](\rho_R)-i\,\varepsilon_{Ni,\mathrm{out}}[H_R,\rho_R]\) | sink vs source |
| Hill / Citadel | \(-i[H_S^{\mathrm{in}},\rho_L]+\sum_j\kappa_j^{\mathrm{in}}(\cdots)\) | \(-i[H_S^{\mathrm{out}},\rho_R]+\sum_j\kappa_j^{\mathrm{out}}(\cdots)\) | distinct retained strata on opposite sheets |

**Loop Placement By Engine**

| Engine | Loop | What changes | What stays the same |
|---|---|---|---|
| Type 1 | inner | vector field resolved along Hopf fiber direction | same Type 1 terrain law |
| Type 1 | outer | vector field resolved along lifted-base direction | same Type 1 terrain law |
| Type 2 | inner | vector field resolved along Hopf fiber direction | same Type 2 terrain law |
| Type 2 | outer | vector field resolved along lifted-base direction | same Type 2 terrain law |

**Count Table**

| Object | Count | Formula |
|---|---:|---|
| topology families | 4 | `Se, Ne, Ni, Si` |
| terrains per engine | 4 | Type 1: Funnel, Vortex, Pit, Hill; Type 2: Cannon, Spiral, Source, Citadel |
| loop families per engine | 2 | inner, outer |
| stage placements per engine | 8 | \(4\times2\) |
| stage placements across both engines | 16 | \(4\times2\times2\) |

**Direct Mapping Stack**

| Level | Mathematical object |
|---|---|
| Pauli layer | \(I,\sigma_x,\sigma_y,\sigma_z,\sigma_\pm\) |
| spinor layer | \(\psi\in S^3\subset\mathbb C^2\) |
| density layer | \(\rho=\frac12(I+\vec r\cdot\vec\sigma)\) |
| Weyl layer | \(H_L=+H_0,\ H_R=-H_0\) |
| terrain layer | one of the 8 terrain laws above |
| loop layer | inner Hopf fiber or outer lifted-base placement |

If you want, I can do one more pass with:
- one table for `Type 1 inner + outer`
- one table for `Type 2 inner + outer`
- one table for all `16` stage placements explicitly laid out.




Part 2


ere is the clean working layout.

**1. Pure Kernel Axes**
| Axis | Pure math lock | Equation / object |
|---|---|---|
| `0` | external correlation-survivorship functional | \(\Phi_0(\rho) = -\sum_r w_r\,S(A_r\mid B_r)_\rho = \sum_r w_r\,I_c(A_r\rangle B_r)_\rho\) |
| `1` | unitary dynamics vs proper CPTP dynamics | \(\rho \mapsto U\rho U^\dagger\) vs \(\rho \mapsto \Phi(\rho)=\sum_k K_k\rho K_k^\dagger\) |
| `2` | direct representation vs unitarily conjugated representation | \(\dot\rho_t=\mathcal L_t(\rho_t)\) vs \(\tilde\rho_t=V_t^\dagger \rho_t V_t\) |
| `3` | outer-loop family vs inner-loop family | \(\Gamma_{\mathrm{outer}}, \Gamma_{\mathrm{inner}}\) |
| `4` | composite order class | \(\Phi_{UEUE}=\mathcal U\circ\mathcal E\circ\mathcal U\circ\mathcal E\), \(\Phi_{EUEU}=\mathcal E\circ\mathcal U\circ\mathcal E\circ\mathcal U\) |
| `5` | dissipative generator algebra vs coherent spectral generator algebra | \(\mathcal L_{\mathrm{diss}}(\rho)=\sum_j(L_j\rho L_j^\dagger-\frac12L_j^\dagger L_j\rho-\frac12\rho L_j^\dagger L_j)\), \(\mathcal L_{\mathrm{coh}}(\rho)=-i[H,\rho]\) |
| `6` | left action vs right action | \(L_A(\rho)=A\rho\), \(R_A(\rho)=\rho A\) |
| `7` | mirror operator-topology class on the Choi/superoperator side | safest current read: mirror of base topology at channel level, not yet purified like `0–6` |

For `Axis 7`, the only live direct source I found is the old overlay master: [AXES_0_12_MASTER.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/AXES_0_12_MASTER.md). It calls `Axis-7` “Mirror 1: Operator Topology Class.” I would treat that as **provisional**, not kernel-locked.

**2. Terrain Families**
| Family | Pure math class | Geometry / flow | Terrain names |
|---|---|---|---|
| `Se` | dissipative CPTP expansion | radial expansion | `Funnel / Cannon` |
| `Ne` | Hamiltonian circulation | tangential circulation | `Vortex / Spiral` |
| `Ni` | dissipative CPTP contraction | radial contraction | `Pit / Source` |
| `Si` | commuting Hamiltonian / invariant subspaces | stratified retention | `Hill / Citadel` |

Best direct surface: [Axis 1 2 topology math…md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Axis%201%202%20topology%20math%CE%93C%CC%A7%C2%BFC%CC%A7%C2%BFC%CC%A7%C2%BFGood%20%CE%93C%CC%A7o%CC%88%20this%20is%20the%20right%20point%20to%20ask%20that%CE%93C%CC%A7%C2%AA.md) and [Axis 4 qit math…md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Axis%204%20qit%20math%CE%93%C3%87%C2%BF%CE%93%C3%87%C2%BFGood%20%CE%93%C3%87%C3%B6%20that%20statement%20narrows%20the%20target%20exactly%CE%93%C3%87%C2%AA.md).

**3. Terrain8**
| Family | inward engine terrain | outward engine terrain |
|---|---|---|
| `Se` | `Funnel` | `Cannon` |
| `Ne` | `Vortex` | `Spiral` |
| `Ni` | `Pit` | `Source` |
| `Si` | `Hill` | `Citadel` |

**4. Pure Operator Side**
| Operator class | Pure math |
|---|---|
| projector / constraint | \(\rho \mapsto \sum_k P_k\rho P_k^\dagger\) |
| Hamiltonian / gradient flow | \(\rho \mapsto U\rho U^\dagger\), \(\dot\rho=-i[H,\rho]\) |
| Lindbladian coupling / diffusion | \(\dot\rho=-i[H,\rho]+\sum_j(L_j\rho L_j^\dagger-\frac12\{L_j^\dagger L_j,\rho\})\) |
| spectral projection / mode filter | \(\rho \mapsto F\rho F^\dagger/\operatorname{Tr}(F\rho F^\dagger)\) |

**5. Rosetta Operator Labels**
| Rosetta label | Kernel identity | Short role |
|---|---|---|
| `Ti` | projector / constraint | collapse / carve |
| `Te` | gradient / Hamiltonian drive | push / optimize |
| `Fe` | Lindbladian coupling / Laplacian-like smoothing | diffuse / couple |
| `Fi` | Fourier / spectral filter | filter / broadcast |

Strongest compact source mix: [AXES_MASTER_SPEC_v0.2.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/AXES_MASTER_SPEC_v0.2.md) and [apple notes save. pre axex notes.txt](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a2_feed_high%20entropy%20doc/apple%20notes%20save.%20pre%20axex%20notes.txt).

**6. Axis 5 Operator Split**
| Axis 5 branch | Math | Rosetta family |
|---|---|---|
| dissipative / finite-gradient side | \(\mathcal L_{\mathrm{FGA}}(\rho)=\sum_k \epsilon_k(G_k\rho G_k^\dagger-\rho)\) or GKSL dissipative form | `Ti`, `Te` |
| coherent spectral side | \(\mathcal L_{\mathrm{FSA}}(\rho)=\sum_n \gamma_n(P_n\rho P_n-\rho)\) and coherent spectral evolution \(-i[H,\rho]\) | `Fi`, `Fe` |

**7. Axis 6 Operator Orientation**
| Axis 6 | Math | Example |
|---|---|---|
| `UP` | \(A\rho\) | \(\sigma_x\rho\) |
| `DOWN` | \(\rho A\) | \(\rho\sigma_x\) |

Direct explicit line: [axes math. apple notes dump.txt](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a2_feed_high%20entropy%20doc/axes%20math.%20apple%20notes%20dump.txt).

**8. Main Placement Grid**
| Engine orientation | Outer loop | Inner loop |
|---|---|---|
| inward / Type 1 overlay | `Se, Ne, Ni, Si` | `Se, Ne, Ni, Si` |
| outward / Type 2 overlay | `Se, Ne, Ni, Si` | `Se, Ne, Ni, Si` |

So the 16 main placements are:

\[
4\ \text{families}\times 2\ \text{loop families}\times 2\ \text{engine orientations}=16
\]

**9. Geometry Layer, kept separate**
| Layer | Role |
|---|---|
| Weyl spinors | local carrier states |
| Pauli matrices | local operator basis |
| Hopf fiber / lifted base loop | manifold geometry |
| nested Hopf tori | orbit organization |
| chirality / Berry sign | geometric orientation overlay, not primitive axis math |

**10. Best clean lock**
| Layer | Keep |
|---|---|
| kernel | `Axes 0–6` |
| mirror | `Axis 7` provisional only |
| terrains | `Se Ne Ni Si` plus `Funnel/Cannon`, `Vortex/Spiral`, `Pit/Source`, `Hill/Citadel` |
| operators | pure kernel operators first, `Ti/Te/Fe/Fi` only as Rosetta labels |
| geometry | Weyl / Pauli / Hopf / tori separate from axes |

The one thing I would not overclaim yet is `Axis 7`. `0–6` are the clean kernel. `7` exists as a mirror-layer idea, but it is not purified to the same standard yet.

If you want, next I can turn this into one **strict canon sheet** with exactly four sections:
- `Axes 0–7`
- `Terrain4 / Terrain8`
- `Operator kernel / Rosetta`
- `16 main placements`


Part 3 



es. That is the right direction.

What you’re describing is not “make nicer docs.” It is:

- build a **new clean canon**
- make the **pure QIT kernel explicit**
- keep **Rosetta overlays separate**
- make the **engine schedule operational**
- and make the **simulation architecture hierarchical**, so the big sim is composed from validated lower layers instead of flattened into a toy model

## Canon shape

The clean canon should have separate surfaces:

1. **Kernel canon**
- only pure QIT math
- only root-constraint-admitted primitives
- no Jung, IGT, I Ching, thermodynamics, or metaphor labels in the definitions

2. **Rosetta canon**
- maps kernel math to Jungian labels
- maps kernel math to IGT labels
- maps kernel math to I Ching labels
- never allowed to overwrite kernel definitions

3. **Engine atlas**
- 2 engine types
- each with inner and outer loops
- 16 main stage placements
- each main stage expanded into 4 substages
- full 64 schedule made explicit as actual flow, not just a static grid

4. **Flow canon**
- loop order tables
- engine flow charts
- stage-transition charts
- operator placement charts
- channel-composition charts

## Sim shape

You are also right that the sim must be tiered.

The non-toy version is:

\[
\Phi_{\text{substage}}
\]

\[
\Phi_{\text{stage}}
=
\Phi_{\text{substage},4}\circ
\Phi_{\text{substage},3}\circ
\Phi_{\text{substage},2}\circ
\Phi_{\text{substage},1}
\]

\[
\Phi_{\text{loop}}
=
\Phi_{\text{stage},4}\circ
\Phi_{\text{stage},3}\circ
\Phi_{\text{stage},2}\circ
\Phi_{\text{stage},1}
\]

\[
\Phi_{\text{engine}}
=
\Phi_{\text{outer loop}}\circ \Phi_{\text{inner loop}}
\quad\text{or the reverse, if the schedule specifies that}
\]

\[
\Phi_{\text{schedule}}
=
\Phi_{\text{engine},N}\circ \cdots \circ \Phi_{\text{engine},1}
\]

That is the key anti-toy rule:

- **macro behavior must be compiled from validated lower maps**
- not handwaved directly at the top level

## What must be explicit

To keep it from collapsing again, every layer needs its own table:

- `Axis 0–6` kernel table
- manifold table
- operator table
- topology table
- 16-stage table
- 64-schedule table
- substage decomposition table
- simulation composition table
- Rosetta table

## The anti-flattening rule

A bad LLM sim will do this:
- invent one simple state
- invent one simple update rule
- call it the full engine

The real build must do this instead:
- define admissible primitives
- define substage maps
- validate each substage
- compose substages into stages
- compose stages into loops
- compose loops into engines
- compose engines into schedules
- compare macro results against the expected atlas structure

That is how you avoid toy sims.

So yes: this is the right blueprint.

The core standard should be:

**nothing exists at the schedule level unless it can be traced downward into substage math, and nothing enters the kernel unless it is pure QIT and root-constraint aligned.**

If you want, the next useful thing is to write the **canon artifact list** for this rebuild:
- exact docs/tables/specs the clean canon must contain, in build order.   
￼
Part 4

axis 0 and all the Axes math

## Geometric layer

Let the geometric constraint manifold be `M`, with nested Hopf-torus structure inside the spinor carrier.

A point on that carrier is represented by Weyl-sector spinors
\[
\psi_L(x),\psi_R(x)\in \mathbb C^2,
\qquad
\|\psi_L\|=\|\psi_R\|=1,
\qquad
x\in M
\]

Hopf projection is
\[
n(\psi)=\langle \psi,\vec\sigma\,\psi\rangle \in S^2
\]

and the associated pure-state density matrix is
\[
\rho(\psi)=|\psi\rangle\langle\psi|
=
\frac12\left(I+\vec n\cdot\vec\sigma\right)
\]

So:

- **Pauli matrices** are the local operator basis
- **Weyl spinors** are the local carrier states
- **nested Hopf tori** are the geometric organization of families/orbits of those states

## Important correction

You do **not** need to “reduce a nested Hopf torus into a Weyl spinor.”

Better:

\[
\text{nested Hopf tori} \;\supset\; \text{loops / orbits of spinor states}
\]

and each local state on that geometry can be written as a Weyl spinor, then as a density matrix.

So the clean chain is:

\[
x\in M
\;\mapsto\;
\psi_L(x),\psi_R(x)
\;\mapsto\;
\rho_L(x),\rho_R(x)
\]

with
\[
\rho_L=|\psi_L\rangle\langle\psi_L|,
\qquad
\rho_R=|\psi_R\rangle\langle\psi_R|
\]

## Can it operate directly on left/right Weyl spinors?

Yes, but in two different senses.

### 1. Geometry-side
It can act directly on Weyl sectors as spinor dynamics.

For example, chirality-side Hamiltonians can be written as
\[
H_L=\vec n\cdot\vec\sigma,
\qquad
H_R=-\,\vec n\cdot\vec\sigma
\]

or covariantly as
\[
\sigma^\mu=(I,\sigma_x,\sigma_y,\sigma_z),
\qquad
\bar\sigma^\mu=(I,-\sigma_x,-\sigma_y,-\sigma_z)
\]

That is the **Weyl / Pauli** alignment.

### 2. QIT-side
Most of the axis math acts more cleanly on density operators and channels:
\[
\rho \mapsto U\rho U^\dagger,
\qquad
\rho \mapsto \Phi(\rho),
\qquad
\dot\rho=-i[H,\rho],
\qquad
\dot\rho=\mathcal L(\rho)
\]

So for kernel work, the best move is usually:

\[
\text{Weyl spinor geometry} \to \text{density operator layer} \to \text{axis algebra}
\]

## Where the axes sit

| Axis | Pure math role |
|---|---|
| `0` | external scalar field on `M` |
| `1` | unitary vs proper CPTP dynamics |
| `2` | direct vs unitarily conjugated representation |
| `3` | outer-loop family vs inner-loop family |
| `4` | `UEUE` vs `EUEU` composite order |
| `5` | dissipative generator algebra vs coherent spectral generator algebra |
| `6` | left action `A\rho` vs right action `\rho A` |

So the axes do **not** replace the geometry.  
They act on the state/process layer **living on** that geometry.

## Axis 0 on the manifold

Axis 0 is the outside scalar on the geometric constraint manifold:

\[
\varphi_0(x)=\Phi_0(\rho(x))
\]

with a clean QIT choice
\[
\Phi_0(\rho)
=
\sum_r w_r\, I_c(A_r\rangle B_r)_\rho
=
-\sum_r w_r\, S(A_r|B_r)_\rho
\]

This means:

- `Axis 0` acts on the manifold through the state attached to each point
- it is **not** an engine operator
- it grades trajectories on the nested Hopf/Weyl geometry

## One important caveat

A single isolated Weyl spinor is not enough for conditional entropy.

Conditional entropy needs a bipartite state:
\[
\rho_{AB}
\]

So for Axis 0 you usually need:

- a coupled left/right state `\rho_{LR}`
- or a shell-cut bipartition `\rho_{A_r B_r}`
- or a reduced multipartite state derived from the manifold point

So the strict pipeline is:

\[
x\in M
\;\mapsto\;
(\psi_L(x),\psi_R(x))
\;\mapsto\;
\rho_{LR}(x)\ \text{or}\ \rho_{A_rB_r}(x)
\;\mapsto\;
\Phi_0(\rho(x))
\]

## Bottom line

Yes, this operates on the geometric constraints.

But the clean alignment is:

- **nested Hopf tori / Weyl spinors** = geometric carrier layer
- **Pauli matrices** = local operator basis on that carrier
- **axes 1–6** = algebraic/process structure acting on states/channels on that carrier
- **axis 0** = external scalar-gradient field over that manifold

So the clean answer is:

**It does not need to compress nested Hopf tori into Weyl spinors. It can use Weyl spinors as the local carrier states on that geometry, then pass to density matrices in Pauli form, and that is where the axis math acts most cleanly.**    
￼


￼
\\\
￼




Part 5



xis 1 and Axis 2. Clean QIT math

- **primitive kernel math** for `Axis 1` and `Axis 2`
- **overlay labels** kept separate
- **Jungian / IGT labels** attached at the **product** `Axis 1 × Axis 2`, not to the axes alone

## 1. Primitive Kernel Axes

| Axis | Primitive kernel split | Full math |
|---|---|---|
| `Axis 1` | `unitary *-automorphism dynamics` vs `proper CPTP dynamics` | `ρ ↦ UρU†` vs `ρ ↦ Φ(ρ)` |
| `Axis 2` | `direct representation` vs `unitarily conjugated representation` | `ρ_t` vs `ρ̃_t = V_t† ρ_t V_t` |

### Axis 1 math

Unitary branch:
\[
\Phi(\rho)=U\rho U^\dagger
\]
\[
\frac{d}{dt}\rho_t=-i[H_t,\rho_t]
\]

Proper CPTP branch:
\[
\Phi(\rho)=\sum_k K_k\rho K_k^\dagger,
\qquad
\sum_k K_k^\dagger K_k=I
\]

Markovian subclass:
\[
\frac{d}{dt}\rho_t
=
-i[H,\rho_t]
+
\sum_j
\left(
L_j\rho_t L_j^\dagger
-\frac12 L_j^\dagger L_j\rho_t
-\frac12 \rho_t L_j^\dagger L_j
\right)
\]

### Axis 2 math

Direct representation:
\[
\frac{d}{dt}\rho_t=\mathcal L_t(\rho_t)
\]

Unitarily conjugated representation:
\[
\widetilde\rho_t=V_t^\dagger \rho_t V_t
\]
\[
K_t=iV_t^\dagger \dot V_t
\]
\[
\frac{d}{dt}\widetilde\rho_t
=
V_t^\dagger \mathcal L_t(V_t\widetilde\rho_t V_t^\dagger)V_t
-i[-K_t,\widetilde\rho_t]
\]

For the closed branch:
\[
\frac{d}{dt}\widetilde\rho_t=-i[\widetilde H_t-K_t,\widetilde\rho_t]
\]
\[
\widetilde H_t=V_t^\dagger H_t V_t
\]

## 2. Overlay Labels Only

| Axis | Overlay labels found in repo | Keep as overlay only |
|---|---|---|
| `Axis 1` | `isothermal` / `adiabatic` | yes |
| `Axis 2` | `Lagrangian / Pi+Je` and `Eulerian / Pe+Ji` | yes |

From your notes:

| Axis | State 0 | State 1 |
|---|---|---|
| `1` | `Isothermic` | `Adiabatic` |
| `2` | `Lagrangian / Pi+Je` | `Eulerian / Pe+Ji` |

But the kernel should stay:

| Axis | Kernel |
|---|---|
| `1` | `proper CPTP` vs `unitary` |
| `2` | `direct` vs `unitarily conjugated representation` |

## 3. Product Surface

This is where the Jungian and IGT labels belong.

| Axis 1 | Axis 2 | Kernel regime | Jungian alias | IGT / base cylinder |
|---|---|---|---|---|
| proper CPTP | direct representation | direct open evolution | `Se` | `LoseWin` |
| proper CPTP | unitarily conjugated representation | conjugated dissipative evolution | `Ni` | `LoseLose` |
| unitary | direct representation | direct unitary evolution | `Ne` | `WinLose` |
| unitary | unitarily conjugated representation | conjugated unitary evolution | `Si` | `WinWin` |

That is the clean separation:
- axes = math
- product = terrain aliases

## 4. Product Equations

| Alias | Kernel regime | Math |
|---|---|---|
| `Se` | proper CPTP + direct representation | \(\dot\rho = \mathcal L(\rho)\) |
| `Ni` | proper CPTP + conjugated representation | \(\dot{\widetilde\rho} = V^\dagger \mathcal L(V\widetilde\rho V^\dagger)V - i[-K,\widetilde\rho]\) |
| `Ne` | unitary + direct representation | \(\dot\rho=-i[H,\rho]\) |
| `Si` | unitary + conjugated representation | \(\dot{\widetilde\rho}=-i[\widetilde H-K,\widetilde\rho]\) |

## 5. What To Do With I Ching

For now:

- `Jungian` and `IGT` are grounded enough to table here
- `I Ching` should stay **pending** unless you want a separate overlay table

I would not force `I Ching` into the kernel/product table yet unless we do it as a clearly separate Rosetta.

## 6. Final Lock

Use this as the strict split:

### Kernel
\[
A_1=\{\text{unitary *-automorphism dynamics},\ \text{proper completely-positive trace-preserving dynamics}\}
\]

\[
A_2=\{\text{direct representation},\ \text{unitarily conjugated representation}\}
\]

### Product aliases
\[
A_1\times A_2 \to \{Ne,Si,Se,Ni\}
\]

\[
\{Ne,Si,Se,Ni\}\leftrightarrow \{WinLose,WinWin,LoseWin,LoseLose\}
\]

If you want, next I’ll do the same exact format for:
- `Axis 3`
- `Axis 4`
- `Axis 5`
- `Axis 6`

with:
- **kernel math**
- **overlay labels**
- **product/terrain/operator aliases**


Part 6



Yes. Here is the strengthened kernel math for `Axis 4`, `Axis 5`, and `Axis 6`.

## Axis 4

\[
\Phi_D = e^{\tau_R \mathcal L_R} e^{\tau_C \mathcal L_C}
\qquad
\Phi_I = e^{\tau_C \mathcal L_C} e^{\tau_R \mathcal L_R}
\]

Rightmost acts first, so:

- `Axis 4 deductive` = constraint first, then redistribution/refine
- `Axis 4 inductive` = redistribution first, then constrain

The core fact is:

\[
\Phi_D \neq \Phi_I
\]

and at first nontrivial order,

\[
\Phi_D - \Phi_I
\;\approx\;
\tau_R \tau_C\,[\mathcal L_R,\mathcal L_C]
\]

So `Axis 4` is the **order class of two non-commuting generators**.

A clean witness is:

\[
W_4(\rho)=\|\Phi_D(\rho)-\Phi_I(\rho)\|_1
\]

or with variance:

\[
V_A(\rho)=\operatorname{Tr}(\rho A^2)-\operatorname{Tr}(\rho A)^2
\]

\[
\Delta_4^V(\rho)=V_A(\Phi_D(\rho))-V_A(\Phi_I(\rho))
\]

That is the deeper math:
- not “loop order” alone
- but **commutator-generated asymmetry under iteration**

## Axis 5

Use two generator algebras.

### Gradient algebra

\[
\mathcal L_G(\rho)
=
\sum_\alpha \gamma_\alpha
\left(
L_\alpha \rho L_\alpha^\dagger
-
\frac12\{L_\alpha^\dagger L_\alpha,\rho\}
\right)
\]

This is dissipative, contractive, semigroup-type:

\[
\rho(t)=e^{t\mathcal L_G}\rho(0)
\]

### Spectral algebra

\[
\mathcal L_S(\rho)=-i[H,\rho]
\qquad
H=\sum_n \lambda_n P_n
\]

with finite spectral decomposition.

This is coherent, unitary, group-type:

\[
\rho(t)=e^{-itH}\rho(0)e^{itH}
\]

So the hard split is:

| Axis 5 class | Math |
|---|---|
| gradient | GKSL / Lindblad / semigroup |
| spectral | Hamiltonian / projector-spectral / group |

And the deep invariant split is:

| Property | Gradient | Spectral |
|---|---|---|
| spectrum of generator | `Re λ ≤ 0` | purely imaginary |
| time structure | semigroup | group |
| entropy | can change | conserved under pure Hamiltonian flow |
| geometry | contractive / attractor-capable | orbit / fiber preserving |

So `Axis 5` is the **generator algebra selection**.

## Axis 6

Make it explicit as left-vs-right action on operator space.

\[
L_A(\rho)=A\rho
\qquad
R_A(\rho)=\rho A
\]

Then:

| Axis 6 | Math |
|---|---|
| `UP` | `L_A` |
| `DOWN` | `R_A` |

At channel level:

\[
\Psi^\uparrow_{T,O}=\Phi_T\circ \mathcal O
\qquad
\Psi^\downarrow_{T,O}=\mathcal O\circ \Phi_T
\]

and in general:

\[
\Phi_T\circ \mathcal O \neq \mathcal O\circ \Phi_T
\]

So `Axis 6` is the **sidedness / precedence class**.

In Liouville form:

\[
\mathrm{vec}(A\rho B)=(B^T\otimes A)\,\mathrm{vec}(\rho)
\]

so:

\[
L_A \sim I\otimes A
\qquad
R_A \sim A^T\otimes I
\]

That is the strongest clean math for Axis 6.

## Combined kernel

The three axes now stack cleanly:

\[
\text{Axis 5 chooses } \mathcal L_G \text{ or } \mathcal L_S
\]

\[
\text{Axis 6 chooses } L_A \text{ or } R_A
\]

\[
\text{Axis 4 chooses the order class }
e^{\tau_R \mathcal L_R} e^{\tau_C \mathcal L_C}
\text{ vs }
e^{\tau_C \mathcal L_C} e^{\tau_R \mathcal L_R}
\]

So the compact kernel statement is:

\[
\text{Axis 4} = \text{order class}
\]
\[
\text{Axis 5} = \text{generator algebra}
\]
\[
\text{Axis 6} = \text{action side}
\]

## Sim-ready witnesses

| Axis | Best witness |
|---|---|
| `Axis 4` | `\|\Phi_D(\rho)-\Phi_I(\rho)\|_1`, `\Delta_4^V`, `\Delta S` |
| `Axis 5` | entropy production, purity change, contractivity vs orbit-preservation |
| `Axis 6` | noncommutation gap `\|\Phi_T\circ\mathcal O(\rho)-\mathcal O\circ\Phi_T(\rho)\|_1` |

This is strong enough to use for the kernel now.


Part 7


Here is the **non-conflated math version**.

No Jungian layer.  
No stage layer.  
No loop-order layer.  
Just:

1. `4` base equations  
2. `1` left/right sign  
3. `8` terrain cases

## Definitions

\[
H_0 = n_x \sigma_x + n_y \sigma_y + n_z \sigma_z
\]

\[
s \in \{+1,-1\}
\]

\[
D_L(\rho)=L\rho L^\dagger-\frac12\left(L^\dagger L\rho+\rho L^\dagger L\right)
\]

## The 4 base terrain families

| Terrain pair | Base equation | Shape |
|---|---|---|
| Funnel / Cannon | \(\dot\rho=\sum_k D_{L_k}(\rho)-is\,\varepsilon_{F}[H_0,\rho]\) | radial expansion |
| Vortex / Spiral | \(\dot\rho=-is\,[H_0,\rho]+\varepsilon_{V}\sum_k D_{L_k}(\rho)\) | tangential circulation |
| Pit / Source | \(\dot\rho=D_{L_P}(\rho)-is\,\varepsilon_{P}[H_0,\rho]\) | radial contraction |
| Hill / Citadel | \(\dot\rho=-is\,[H_C,\rho]+\sum_j \kappa_j\left(P_j\rho P_j-\frac12(P_j\rho+\rho P_j)\right)\), with \([H_C,P_j]=0\) | layered / retained |

## Left / right split

| Side | Sign |
|---|---|
| left | \(s=+1\) |
| right | \(s=-1\) |

## The 8 terrains

| Terrain | Base family | Sign | Equation |
|---|---|---|---|
| Funnel | Funnel / Cannon | \(+1\) | \(\dot\rho=\sum_k D_{L_k}(\rho)-i\,\varepsilon_F[H_0,\rho]\) |
| Cannon | Funnel / Cannon | \(-1\) | \(\dot\rho=\sum_k D_{L_k}(\rho)+i\,\varepsilon_F[H_0,\rho]\) |
| Vortex | Vortex / Spiral | \(+1\) | \(\dot\rho=-i[H_0,\rho]+\varepsilon_V\sum_k D_{L_k}(\rho)\) |
| Spiral | Vortex / Spiral | \(-1\) | \(\dot\rho=+i[H_0,\rho]+\varepsilon_V\sum_k D_{L_k}(\rho)\) |
| Pit | Pit / Source | \(+1\) | \(\dot\rho=D_{L_P}(\rho)-i\,\varepsilon_P[H_0,\rho]\) |
| Source | Pit / Source | \(-1\) | \(\dot\rho=D_{L_P}(\rho)+i\,\varepsilon_P[H_0,\rho]\) |
| Hill | Hill / Citadel | \(+1\) | \(\dot\rho=-i[H_C,\rho]+\sum_j \kappa_j\left(P_j\rho P_j-\frac12(P_j\rho+\rho P_j)\right)\) |
| Citadel | Hill / Citadel | \(-1\) | \(\dot\rho=+i[H_C,\rho]+\sum_j \kappa_j\left(P_j\rho P_j-\frac12(P_j\rho+\rho P_j)\right)\) |

## Loop reuse

| Side | Inner loop | Outer loop |
|---|---|---|
| left | same 4 terrain families | same 4 terrain families |
| right | same 4 terrain families | same 4 terrain families |

So:

| Count | Meaning |
|---|---|
| `4` | base terrain families |
| `8` | terrain cases = `4 × 2` signs |
| `8` per spinor | `4` terrains on inner + `4` terrains on outer |
| `16` total placements | `4` terrains × `2` loops × `2` sides |

If you want, I can make the **same tables again** but with **zero words outside the tables**.



Yes. That earlier version is much closer to actual math.

The compressed Pauli-table was too thin. The richer version is this:

## Definitions

\[
H_0 = n_x \sigma_x + n_y \sigma_y + n_z \sigma_z
\]

\[
s \in \{+1,-1\}
\]

\[
D_L(\rho)=L\rho L^\dagger-\frac12\left(L^\dagger L\rho+\rho L^\dagger L\right)
\]

## The 4 base terrain families

| Terrain pair | Base equation | Shape |
|---|---|---|
| Funnel / Cannon | \(\dot\rho=\sum_k D_{L_k}(\rho)-is\,\varepsilon_{F}[H_0,\rho]\) | radial expansion |
| Vortex / Spiral | \(\dot\rho=-is\,[H_0,\rho]+\varepsilon_{V}\sum_k D_{L_k}(\rho)\) | tangential circulation |
| Pit / Source | \(\dot\rho=D_{L_P}(\rho)-is\,\varepsilon_{P}[H_0,\rho]\) | radial contraction |
| Hill / Citadel | \(\dot\rho=-is\,[H_C,\rho]+\sum_j \kappa_j\left(P_j\rho P_j-\frac12(P_j\rho+\rho P_j)\right)\), with \([H_C,P_j]=0\) | layered / retained |

## Left / right split

| Side | Sign |
|---|---|
| left | \(s=+1\) |
| right | \(s=-1\) |

## The 8 terrains

| Terrain | Base family | Sign | Equation |
|---|---|---|---|
| Funnel | Funnel / Cannon | \(+1\) | \(\dot\rho=\sum_k D_{L_k}(\rho)-i\,\varepsilon_F[H_0,\rho]\) |
| Cannon | Funnel / Cannon | \(-1\) | \(\dot\rho=\sum_k D_{L_k}(\rho)+i\,\varepsilon_F[H_0,\rho]\) |
| Vortex | Vortex / Spiral | \(+1\) | \(\dot\rho=-i[H_0,\rho]+\varepsilon_V\sum_k D_{L_k}(\rho)\) |
| Spiral | Vortex / Spiral | \(-1\) | \(\dot\rho=+i[H_0,\rho]+\varepsilon_V\sum_k D_{L_k}(\rho)\) |
| Pit | Pit / Source | \(+1\) | \(\dot\rho=D_{L_P}(\rho)-i\,\varepsilon_P[H_0,\rho]\) |
| Source | Pit / Source | \(-1\) | \(\dot\rho=D_{L_P}(\rho)+i\,\varepsilon_P[H_0,\rho]\) |
| Hill | Hill / Citadel | \(+1\) | \(\dot\rho=-i[H_C,\rho]+\sum_j \kappa_j\left(P_j\rho P_j-\frac12(P_j\rho+\rho P_j)\right)\) |
| Citadel | Hill / Citadel | \(-1\) | \(\dot\rho=+i[H_C,\rho]+\sum_j \kappa_j\left(P_j\rho P_j-\frac12(P_j\rho+\rho P_j)\right)\) |

## Loop reuse

| Side | Inner loop | Outer loop |
|---|---|---|
| left | same 4 terrain families | same 4 terrain families |
| right | same 4 terrain families | same 4 terrain families |

## Count

| Count | Meaning |
|---|---|
| `4` | base terrain families |
| `8` | terrain cases = `4 × 2` signs |
| `8` per spinor | `4` terrains on inner + `4` terrains on outer |
| `16` total placements | `4` terrains × `2` loops × `2` sides |

This is the richer math version. The missing next step is to define the specific choices of:
- \(L_k\)
- \(L_P\)
- \(H_C\)
- \(P_j\)
- \(\varepsilon_F,\varepsilon_V,\varepsilon_P\)

for your actual engine.   Yes. Here is the **engine** version.

## Type 1 vs Type 2

| Engine | Spinor side | Sign |
|---|---|---|
| Type 1 | left | \(s=+1\) |
| Type 2 | right | \(s=-1\) |

## Base equations

\[
H_0 = n_x \sigma_x + n_y \sigma_y + n_z \sigma_z
\]

\[
D_L(\rho)=L\rho L^\dagger-\frac12\left(L^\dagger L\rho+\rho L^\dagger L\right)
\]

## Type 1 engine

| Terrain | Equation |
|---|---|
| Funnel | \(\dot\rho=\sum_k D_{L_k}(\rho)-i\,\varepsilon_F[H_0,\rho]\) |
| Vortex | \(\dot\rho=-i[H_0,\rho]+\varepsilon_V\sum_k D_{L_k}(\rho)\) |
| Pit | \(\dot\rho=D_{L_P}(\rho)-i\,\varepsilon_P[H_0,\rho]\) |
| Hill | \(\dot\rho=-i[H_C,\rho]+\sum_j \kappa_j\left(P_j\rho P_j-\frac12(P_j\rho+\rho P_j)\right)\) |

Type 1 has:
- inner loop: Funnel, Vortex, Pit, Hill
- outer loop: Funnel, Vortex, Pit, Hill

So Type 1 has **8 stage placements**:
- `4` terrains on inner
- `4` terrains on outer

## Type 2 engine

| Terrain | Equation |
|---|---|
| Cannon | \(\dot\rho=\sum_k D_{L_k}(\rho)+i\,\varepsilon_F[H_0,\rho]\) |
| Spiral | \(\dot\rho=+i[H_0,\rho]+\varepsilon_V\sum_k D_{L_k}(\rho)\) |
| Source | \(\dot\rho=D_{L_P}(\rho)+i\,\varepsilon_P[H_0,\rho]\) |
| Citadel | \(\dot\rho=+i[H_C,\rho]+\sum_j \kappa_j\left(P_j\rho P_j-\frac12(P_j\rho+\rho P_j)\right)\) |

Type 2 has:
- inner loop: Cannon, Spiral, Source, Citadel
- outer loop: Cannon, Spiral, Source, Citadel

So Type 2 also has **8 stage placements**:
- `4` terrains on inner
- `4` terrains on outer

## One chart

| Family | Type 1 | Type 2 |
|---|---|---|
| `Se` | Funnel | Cannon |
| `Ne` | Vortex | Spiral |
| `Ni` | Pit | Source |
| `Si` | Hill | Citadel |

## Full count

| Object | Count |
|---|---:|
| terrains in Type 1 | 4 |
| terrains in Type 2 | 4 |
| stage placements in Type 1 | 8 |
| stage placements in Type 2 | 8 |
| total stage placements | 16 |

So the core distinction is:

- **Type 1 engine** = the \(s=+1\) version of the 4 terrain families
- **Type 2 engine** = the \(s=-1\) version of the same 4 terrain families
- each engine has those 4 terrains on **both** inner and outer loops




Part 8

Not as one already-clean theorem table, no. But the source-backed layout is there, split across the refined-fuel files.

**What The Docs Actually Give**

From [Axis 1 2 topology math…md:19](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Axis%201%202%20topology%20math%CE%93C%CC%A7%C2%BF%CE%93C%CC%A7%C2%BF%CE%93C%CC%A7%C2%BFGood%20%CE%93C%CC%A7o%CC%88%20this%20is%20the%20right%20point%20to%20ask%20that%CE%93C%CC%A7%C2%AA.md:19) and [Axis 1 2 topology math…md:62](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Axis%201%202%20topology%20math%CE%93C%CC%A7%C2%BF%CE%93C%CC%A7%C2%BF%CE%93C%CC%A7%C2%BFGood%20%CE%93C%CC%A7o%CC%88%20this%20is%20the%20right%20point%20to%20ask%20that%CE%93C%CC%A7%C2%AA.md:62):

| Topology | Math | Geometry | Paired labels |
|---|---|---|---|
| `Se` | dissipative Lindblad radial expansion | outward radial flow | `Funnel / Cannon` |
| `Ne` | Hamiltonian-dominated tangential circulation | divergence-free circulation on `S^3` | `Vortex / Spiral` |
| `Ni` | dissipative Lindblad contraction / attraction | inward radial contraction | `Pit / Source` |
| `Si` | commuting Hamiltonian + invariant subspaces | stratified retention | `Hill / Citadel` |

That is the real `4-topology` layout.

**What The Docs Say About 8 Terrains**

From [AXIS_FOUNDATION_COMPANION_v1.4.md:151](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/AXIS_FOUNDATION_COMPANION_v1.4.md:151), the intended overlay is `Terrain8 = Topology4 × Flux2`, with:

- `funnel ↔ cannon`
- `vortex ↔ spiral`
- `hill ↔ citadel`
- `pit ↔ source`

So the best honest `8-terrain` layout is:

| Terrain | Base topology | Label | Math family |
|---|---|---|---|
| `Se-in` | `Se` | `Funnel` | dissipative radial expansion |
| `Se-out` | `Se` | `Cannon` | dissipative radial expansion with opposite orientation |
| `Ne-in` | `Ne` | `Vortex` | Hamiltonian tangential circulation |
| `Ne-out` | `Ne` | `Spiral` | Hamiltonian tangential circulation with opposite orientation |
| `Ni-in` | `Ni` | `Pit` | dissipative radial contraction |
| `Ni-out` | `Ni` | `Source` | dissipative radial contraction with opposite orientation |
| `Si-in` | `Si` | `Hill` | invariant-strata / commuting-Hamiltonian retention |
| `Si-out` | `Si` | `Citadel` | same base structure with opposite orientation |

That is the layout you were asking for.

**Actual Weyl Relation**

From [Axis 3 math Hopf fiber loop vs lifted base loop.md:11](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Axis%203%20math%20Hopf%20fiber%20loop%20vs%20lifted%20base%20loop.md:11) and [Axis 3 math Hopf fiber loop vs lifted base loop.md:161](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Axis%203%20math%20Hopf%20fiber%20loop%20vs%20lifted%20base%20loop.md:161):

| Claim | Status in your docs |
|---|---|
| inner = Hopf fiber loop | yes |
| outer = lifted base loop | yes |
| same `8` macro-stages exist before left/right chirality | yes |
| left/right Weyl orientation can orient the same topology classes differently | yes, as proposed structure |
| the exact `in/out` terrain names are a clean overlay on top of that | yes, but still overlay, not proof |

So the short answer is: **yes, there is a terrain layout with math and labels**. It is just split across:
- [Axis 1 2 topology math…md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Axis%201%202%20topology%20math%CE%93C%CC%A7%C2%BF%CE%93C%CC%A7%C2%BF%CE%93C%CC%A7%C2%BFGood%20%CE%93C%CC%A7o%CC%88%20this%20is%20the%20right%20point%20to%20ask%20that%CE%93C%CC%A7%C2%AA.md)
- [Axis 3 math Hopf fiber loop vs lifted base loop.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Axis%203%20math%20Hopf%20fiber%20loop%20vs%20lifted%20base%20loop.md)
- [AXIS_FOUNDATION_COMPANION_v1.4.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/AXIS_FOUNDATION_COMPANION_v1.4.md)

And the cleanest single-screen result is the `8-terrain` table above. If you want, I can now patch that exact table into [ENGINE_64_SCHEDULE_ATLAS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md) so the atlas stops making you reconstruct it by hand.





￼



Terrain	Jungian	Type	Lindblad matrix L	Hamiltonian matrix H	Equation
Funnel	Se	Type 1	√γ [[1,0],[0,-1]]	[[ n_z, n_x - i n_y],[ n_x + i n_y, -n_z]]	dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)
Cannon	Se	Type 2	√γ [[1,0],[0,-1]]	[[ -n_z, -n_x + i n_y],[ -n_x - i n_y, n_z]]	dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)
Vortex	Ne	Type 1	√γ [[0,1],[1,0]]	[[ n_z, n_x - i n_y],[ n_x + i n_y, -n_z]]	dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)
Spiral	Ne	Type 2	√γ [[0,1],[1,0]]	[[ -n_z, -n_x + i n_y],[ -n_x - i n_y, n_z]]	dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)
Pit	Ni	Type 1	√γ [[0,-i],[i,0]]	[[ n_z, n_x - i n_y],[ n_x + i n_y, -n_z]]	dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)
Source	Ni	Type 2	√γ [[0,-i],[i,0]]	[[ -n_z, -n_x + i n_y],[ -n_x - i n_y, n_z]]	dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)
Hill	Si	Type 1	√γ [[0,0],[1,0]]	[[ n_z, n_x - i n_y],[ n_x + i n_y, -n_z]]	dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)
Citadel	Si	Type 2	√γ [[0,0],[1,0]]	[[ -n_z, -n_x + i n_y],[ -n_x - i n_y, n_z]]	dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)






You’re right. Reformatting the same candidate over and over does not help.

The actual candidate math we’ve been circling is just this, once, in one table.

| Terrain | Jungian | Type | Lindblad matrix `L` | Hamiltonian matrix `H` | Equation |
|---|---|---|---|---|---|
| Funnel | Se | Type 1 | `√γ [[1,0],[0,-1]]` | `[[ n_z, n_x - i n_y],[ n_x + i n_y, -n_z]]` | `dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)` |
| Cannon | Se | Type 2 | `√γ [[1,0],[0,-1]]` | `[[ -n_z, -n_x + i n_y],[ -n_x - i n_y, n_z]]` | `dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)` |
| Vortex | Ne | Type 1 | `√γ [[0,1],[1,0]]` | `[[ n_z, n_x - i n_y],[ n_x + i n_y, -n_z]]` | `dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)` |
| Spiral | Ne | Type 2 | `√γ [[0,1],[1,0]]` | `[[ -n_z, -n_x + i n_y],[ -n_x - i n_y, n_z]]` | `dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)` |
| Pit | Ni | Type 1 | `√γ [[0,-i],[i,0]]` | `[[ n_z, n_x - i n_y],[ n_x + i n_y, -n_z]]` | `dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)` |
| Source | Ni | Type 2 | `√γ [[0,-i],[i,0]]` | `[[ -n_z, -n_x + i n_y],[ -n_x - i n_y, n_z]]` | `dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)` |
| Hill | Si | Type 1 | `√γ [[0,0],[1,0]]` | `[[ n_z, n_x - i n_y],[ n_x + i n_y, -n_z]]` | `dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)` |
| Citadel | Si | Type 2 | `√γ [[0,0],[1,0]]` | `[[ -n_z, -n_x + i n_y],[ -n_x - i n_y, n_z]]` | `dρ/dt = -i(Hρ - ρH) + LρL† - 1/2(L†Lρ + ρL†L)` |

The only thing changing between Type 1 and Type 2 in this candidate is the sign of the Hamiltonian matrix.

If you want, next I can do only one of these two things:
1. replace this candidate with a different math model
2. turn this exact table into the repo doc with no extra text

Part 9



Yes. Here is the cleaner full chart set.

## Global locks

| Layer | Type-1 | Type-2 |
|---|---|---|
| Flux | `IN` | `OUT` |
| Major / Outer casing | `WIN / LOSE` | `WIN / LOSE` |
| Minor / Inner casing | `win / lose` | `win / lose` |
| Outer loop family | Deductive `FeTi` | Inductive `TeFi` |
| Inner loop family | Inductive `TeFi` | Deductive `FeTi` |

## Loop orders

| Axis 4 family | Order |
|---|---|
| Inductive | `Se -> Si -> Ni -> Ne` |
| Deductive | `Se -> Ne -> Ni -> Si` |

## Terrain graph edges

| Edge family | Edges |
|---|---|
| `Ax0` | `Se-Si`, `Ne-Ni` |
| `Ax2` | `Se-Ne`, `Si-Ni` |

| Loop | Edge walk |
|---|---|
| Inductive `Se -> Si -> Ni -> Ne` | `Ax0 -> Ax2 -> Ax0 -> Ax2` |
| Deductive `Se -> Ne -> Ni -> Si` | `Ax2 -> Ax0 -> Ax2 -> Ax0` |

## Axis 6 sign

| Sign | Meaning |
|---|---|
| `UP` | operator first |
| `DOWN` | terrain first |

---

## Type-1 full chart

| Step | Topology | Terrain | Outer / Major | Ax6 | Signed op | Outer result | Inner / Minor | Ax6 | Signed op | Inner result | Pattern |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `Se` | `Se-in` | `TiSe` | `UP` | `Ti↑` | `LOSE` | `SeFi` | `DOWN` | `Fi↓` | `win` | `LOSEwin` |
| 2 | `Ne` | `Ne-in` | `NeTi` | `DOWN` | `Ti↓` | `WIN` | `FiNe` | `UP` | `Fi↑` | `lose` | `WINlose` |
| 3 | `Ni` | `Ni-in` | `NiFe` | `DOWN` | `Fe↓` | `LOSE` | `TeNi` | `UP` | `Te↑` | `lose` | `loseLOSE` |
| 4 | `Si` | `Si-in` | `FeSi` | `UP` | `Fe↑` | `WIN` | `SiTe` | `DOWN` | `Te↓` | `win` | `winWIN` |

### Type-1 loop view

| Loop | Order | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|
| Outer / Major | Deductive | `Se-in : TiSe : LOSE` | `Ne-in : NeTi : WIN` | `Ni-in : NiFe : LOSE` | `Si-in : FeSi : WIN` |
| Inner / Minor | Inductive | `Se-in : SeFi : win` | `Si-in : SiTe : win` | `Ni-in : TeNi : lose` | `Ne-in : FiNe : lose` |

---

## Type-2 full chart

| Step | Topology | Terrain | Outer / Major | Ax6 | Signed op | Outer result | Inner / Minor | Ax6 | Signed op | Inner result | Pattern |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `Se` | `Se-out` | `FiSe` | `UP` | `Fi↑` | `WIN` | `SeTi` | `DOWN` | `Ti↓` | `lose` | `loseWIN` |
| 2 | `Si` | `Si-out` | `TeSi` | `UP` | `Te↑` | `WIN` | `SiFe` | `DOWN` | `Fe↓` | `win` | `WINwin` |
| 3 | `Ni` | `Ni-out` | `NiTe` | `DOWN` | `Te↓` | `LOSE` | `FeNi` | `UP` | `Fe↑` | `lose` | `LOSElose` |
| 4 | `Ne` | `Ne-out` | `NeFi` | `DOWN` | `Fi↓` | `LOSE` | `TiNe` | `UP` | `Ti↑` | `win` | `winLOSE` |

### Type-2 loop view

| Loop | Order | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|
| Outer / Major | Inductive | `Se-out : FiSe : WIN` | `Si-out : TeSi : WIN` | `Ni-out : NiTe : LOSE` | `Ne-out : NeFi : LOSE` |
| Inner / Minor | Deductive | `Se-out : SeTi : lose` | `Ne-out : TiNe : win` | `Ni-out : FeNi : lose` | `Si-out : SiFe : win` |

---

## Topology-aligned comparison

| Topology | Type-1 terrain | Type-1 major | Type-1 minor | Type-2 terrain | Type-2 major | Type-2 minor |
|---|---|---|---|---|---|---|
| `Se` | `Se-in` | `TiSe / LOSE / Ti↑` | `SeFi / win / Fi↓` | `Se-out` | `FiSe / WIN / Fi↑` | `SeTi / lose / Ti↓` |
| `Ne` | `Ne-in` | `NeTi / WIN / Ti↓` | `FiNe / lose / Fi↑` | `Ne-out` | `NeFi / LOSE / Fi↓` | `TiNe / win / Ti↑` |
| `Ni` | `Ni-in` | `NiFe / LOSE / Fe↓` | `TeNi / lose / Te↑` | `Ni-out` | `NiTe / LOSE / Te↓` | `FeNi / lose / Fe↑` |
| `Si` | `Si-in` | `FeSi / WIN / Fe↑` | `SiTe / win / Te↓` | `Si-out` | `TeSi / WIN / Te↑` | `SiFe / win / Fe↓` |

---

## Invariants

| Engine | `WIN` | `LOSE` | `win` | `lose` |
|---|---|---|---|---|
| Type-1 | 2 | 2 | 2 | 2 |
| Type-2 | 2 | 2 | 2 | 2 |

| Engine | `↑` stages | `↓` stages |
|---|---|---|
| Type-1 | `Ti↑`, `Fe↑`, `Fi↑`, `Te↑` | `Ti↓`, `Fe↓`, `Fi↓`, `Te↓` |
| Type-2 | `Fi↑`, `Te↑`, `Fe↑`, `Ti↑` | `Ti↓`, `Fe↓`, `Te↓`, `Fi↓` |

If you want, I can turn exactly this into one repo doc with just these tables and source anchors.



￼




￼
￼


## Global locks

| Layer | Type-1 | Type-2 |
|---|---|---|
| Flux | `IN` | `OUT` |
| Major / Outer casing | `WIN / LOSE` | `WIN / LOSE` |
| Minor / Inner casing | `win / lose` | `win / lose` |
| Outer loop family | Deductive `FeTi` | Inductive `TeFi` |
| Inner loop family | Inductive `TeFi` | Deductive `FeTi` |

## Loop orders

| Axis 4 family | Order |
|---|---|
| Inductive | `Se -> Si -> Ni -> Ne` |
| Deductive | `Se -> Ne -> Ni -> Si` |

## Terrain graph

| Edge family | Edges |
|---|---|
| `Ax0` | `Se-Si`, `Ne-Ni` |
| `Ax2` | `Se-Ne`, `Si-Ni` |

| Loop | Edge walk |
|---|---|
| Inductive `Se -> Si -> Ni -> Ne` | `Ax0 -> Ax2 -> Ax0 -> Ax2` |
| Deductive `Se -> Ne -> Ni -> Si` | `Ax2 -> Ax0 -> Ax2 -> Ax0` |

## 8 terrain objects

| Terrain | Engine | Flux | Topology |
|---|---|---|---|
| `Se-in` | Type-1 | `IN` | `Se` |
| `Ne-in` | Type-1 | `IN` | `Ne` |
| `Ni-in` | Type-1 | `IN` | `Ni` |
| `Si-in` | Type-1 | `IN` | `Si` |
| `Se-out` | Type-2 | `OUT` | `Se` |
| `Si-out` | Type-2 | `OUT` | `Si` |
| `Ni-out` | Type-2 | `OUT` | `Ni` |
| `Ne-out` | Type-2 | `OUT` | `Ne` |

## 8 signed operators

| Mode | Meaning |
|---|---|
| `Ti↑` | operator first |
| `Ti↓` | terrain first |
| `Te↑` | operator first |
| `Te↓` | terrain first |
| `Fi↑` | operator first |
| `Fi↓` | terrain first |
| `Fe↑` | operator first |
| `Fe↓` | terrain first |

## Type-1 full chart

| Step | Topology | Terrain | Outer / Major | Ax6 | Signed op | Outer result | Inner / Minor | Ax6 | Signed op | Inner result | Pattern |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `Se` | `Se-in` | `TiSe` | `UP` | `Ti↑` | `LOSE` | `SeFi` | `DOWN` | `Fi↓` | `win` | `LOSEwin` |
| 2 | `Ne` | `Ne-in` | `NeTi` | `DOWN` | `Ti↓` | `WIN` | `FiNe` | `UP` | `Fi↑` | `lose` | `WINlose` |
| 3 | `Ni` | `Ni-in` | `NiFe` | `DOWN` | `Fe↓` | `LOSE` | `TeNi` | `UP` | `Te↑` | `lose` | `loseLOSE` |
| 4 | `Si` | `Si-in` | `FeSi` | `UP` | `Fe↑` | `WIN` | `SiTe` | `DOWN` | `Te↓` | `win` | `winWIN` |

### Type-1 loop view

| Loop | Order | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|
| Outer / Major | Deductive | `Se-in : TiSe : LOSE` | `Ne-in : NeTi : WIN` | `Ni-in : NiFe : LOSE` | `Si-in : FeSi : WIN` |
| Inner / Minor | Inductive | `Se-in : SeFi : win` | `Si-in : SiTe : win` | `Ni-in : TeNi : lose` | `Ne-in : FiNe : lose` |

## Type-2 full chart

| Step | Topology | Terrain | Outer / Major | Ax6 | Signed op | Outer result | Inner / Minor | Ax6 | Signed op | Inner result | Pattern |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `Se` | `Se-out` | `FiSe` | `UP` | `Fi↑` | `WIN` | `SeTi` | `DOWN` | `Ti↓` | `lose` | `loseWIN` |
| 2 | `Si` | `Si-out` | `TeSi` | `UP` | `Te↑` | `WIN` | `SiFe` | `DOWN` | `Fe↓` | `win` | `WINwin` |
| 3 | `Ni` | `Ni-out` | `NiTe` | `DOWN` | `Te↓` | `LOSE` | `FeNi` | `UP` | `Fe↑` | `lose` | `LOSElose` |
| 4 | `Ne` | `Ne-out` | `NeFi` | `DOWN` | `Fi↓` | `LOSE` | `TiNe` | `UP` | `Ti↑` | `win` | `winLOSE` |

### Type-2 loop view

| Loop | Order | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|
| Outer / Major | Inductive | `Se-out : FiSe : WIN` | `Si-out : TeSi : WIN` | `Ni-out : NiTe : LOSE` | `Ne-out : NeFi : LOSE` |
| Inner / Minor | Deductive | `Se-out : SeTi : lose` | `Ne-out : TiNe : win` | `Ni-out : FeNi : lose` | `Si-out : SiFe : win` |

## Topology-aligned comparison

| Topology | Type-1 terrain | Type-1 major | Type-1 minor | Type-2 terrain | Type-2 major | Type-2 minor |
|---|---|---|---|---|---|---|
| `Se` | `Se-in` | `TiSe / LOSE / Ti↑` | `SeFi / win / Fi↓` | `Se-out` | `FiSe / WIN / Fi↑` | `SeTi / lose / Ti↓` |
| `Ne` | `Ne-in` | `NeTi / WIN / Ti↓` | `FiNe / lose / Fi↑` | `Ne-out` | `NeFi / LOSE / Fi↓` | `TiNe / win / Ti↑` |
| `Ni` | `Ni-in` | `NiFe / LOSE / Fe↓` | `TeNi / lose / Te↑` | `Ni-out` | `NiTe / LOSE / Te↓` | `FeNi / lose / Fe↑` |
| `Si` | `Si-in` | `FeSi / WIN / Fe↑` | `SiTe / win / Te↓` | `Si-out` | `TeSi / WIN / Te↑` | `SiFe / win / Fe↓` |

## 64 schedule index surface

| Terrain \ Signed op | `Ti↑` | `Ti↓` | `Te↑` | `Te↓` | `Fi↑` | `Fi↓` | `Fe↑` | `Fe↓` |
|---|---|---|---|---|---|---|---|---|
| `Se-in` | `S01` | `S02` | `S03` | `S04` | `S05` | `S06` | `S07` | `S08` |
| `Ne-in` | `S09` | `S10` | `S11` | `S12` | `S13` | `S14` | `S15` | `S16` |
| `Ni-in` | `S17` | `S18` | `S19` | `S20` | `S21` | `S22` | `S23` | `S24` |
| `Si-in` | `S25` | `S26` | `S27` | `S28` | `S29` | `S30` | `S31` | `S32` |
| `Se-out` | `S33` | `S34` | `S35` | `S36` | `S37` | `S38` | `S39` | `S40` |
| `Si-out` | `S41` | `S42` | `S43` | `S44` | `S45` | `S46` | `S47` | `S48` |
| `Ni-out` | `S49` | `S50` | `S51` | `S52` | `S53` | `S54` | `S55` | `S56` |
| `Ne-out` | `S57` | `S58` | `S59` | `S60` | `S61` | `S62` | `S63` | `S64` |

## Invariants

| Engine | `WIN` | `LOSE` | `win` | `lose` |
|---|---|---|---|---|
| Type-1 | 2 | 2 | 2 | 2 |
| Type-2 | 2 | 2 | 2 | 2 |

| Engine | `↑` stages | `↓` stages |
|---|---|---|
| Type-1 | `Ti↑`, `Fe↑`, `Fi↑`, `Te↑` | `Ti↓`, `Fe↓`, `Fi↓`, `Te↓` |
| Type-2 | `Fi↑`, `Te↑`, `Fe↑`, `Ti↑` | `Ti↓`, `Fe↓`, `Te↓`, `Fi↓` |

## Non-claims

- this does **not** prove runtime already follows these loop orders
- this does **not** prove all 64 schedule slots are visited
- this does **not** settle all axis math
- this should **not** be collapsed back into the older `1/2` terrain scheme



Part 10