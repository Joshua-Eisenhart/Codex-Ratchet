# Screenshots Math Report

Status: DATED CANDIDATE MATERIAL from the owner’s ~2026-03 working screenshots. This report transcribes and compares; it does not promote anything to current, canonical, or complete math.

Scope checked:

- Images checked: all 26 files under `system_v5/READ ONLY Reference Docs/Screenshots/`.
- Current operator baseline checked: `system_v5/READ ONLY Reference Docs/operator math explicit.md`, whose current intrinsic set is exactly `Ti = D_z` dephase, `Te = D_x` dephase, `Fi = R_x`, `Fe = R_z`.
- Probe drift search checked: `rg` over `system_v4/probes/` for `spectral`, `gradient`, `hot_isotherm`, `cold_isotherm`, `H_wave`, `line`, and `wave`.
- Current-map search checked: `rg` over `system_v5/READ ONLY Reference Docs/` for `Axis 0`, `Axis 3`, `Axis 5`, `Axis 6`, `Flux2`, `spectral`, `gradient`, `hot`, `cool`, `line`, and `wave`.
- Absence claims below mean absent from those 26 images by visual inspection and absent from the searches just named.

## 1. Per-Image Transcription

### `0. - (o, tio,).png`

This image is the same carrier/Pauli page content as `Screenshot 2026-03-28 at 1.25.58 PM.png`.

Carrier table:

| Object | Formula | Meaning |
|---|---|---|
| spinor carrier | `psi in C^2, ||psi|| = 1` | normalized 2-spinor |
| pure-state manifold | `S^3 = {psi in C^2 : ||psi|| = 1}` | carrier space |
| Hopf projection | `pi(psi) = psi^dagger vec(sigma) psi in S^2` | Bloch-sphere projection |
| density matrix | unreadable/garbled as `\rho(\psi)=` | meaning cell reads `\psi\rangle\langle\psi`; intended candidate appears to be `rho(psi)=|psi><psi|` |
| Pauli basis | `vec(sigma) = (sigma_x, sigma_y, sigma_z)` | local operator basis |

Pauli matrices:

```latex
I = [[1,0],[0,1]]
sigma_x = [[0,1],[1,0]]
sigma_y = [[0,-i],[i,0]]
sigma_z = [[1,0],[0,-1]]
sigma_- = [[0,0],[1,0]]
sigma_+ = [[0,1],[0,0]]
```

### `1(0) -1021 - 3(1 +7-0).png`

Header: “Use this manifold embedding.”

Carrier:

```latex
S^3 = { psi in C^2 : ||psi|| = 1 }
pi(psi) = psi^dagger vec(sigma) psi in S^2
rho(psi) = |psi><psi| = 1/2 (I + vec(r) . vec(sigma))
vec(sigma) = (sigma_x, sigma_y, sigma_z)
```

Nested Hopf-torus family:

```latex
T_eta = { (e^{i alpha} cos eta, e^{i beta} sin eta) : alpha, beta in S^1 } subset S^3
```

With:

- inner loop = Hopf fiber loop
- outer loop = lifted base loop

Weyl sectors:

```latex
rho_L = 1/2 (I + vec(r)_L . vec(sigma))
rho_R = 1/2 (I + vec(r)_R . vec(sigma))

H_0 = n_x sigma_x + n_y sigma_y + n_z sigma_z
H_L = +H_0
H_R = -H_0
```

### `Can it operate directly on leftjright Weyt spinors.png`

Heading: “Can it operate directly on left/right Weyl spinors?”

Answer text:

- “Yes, but in two different senses.”
- Geometry-side: “It can act directly on Weyl sectors as spinor dynamics.”

Geometry-side formulas:

```latex
H_L = vec(n) . vec(sigma)
H_R = - vec(n) . vec(sigma)

sigma^mu = (I, sigma_x, sigma_y, sigma_z)
bar(sigma)^mu = (I, -sigma_x, -sigma_y, -sigma_z)
```

Text: “That is the Weyl / Pauli alignment.”

QIT-side:

```latex
rho -> U rho U^dagger
rho -> Phi(rho)
dot(rho) = -i[H, rho]
dot(rho) = L(rho)
```

Kernel work pipeline:

```text
Weyl spinor geometry -> density operator layer -> axis algebra
```

Where the axes sit:

| Axis | Pure math role |
|---|---|
| 0 | external scalar field on `M` |
| 1 | unitary vs proper CPTP dynamics |
| 2 | direct vs unitarily conjugated representation |
| 3 | outer-loop family vs inner-loop family |
| 4 | `UEUE` vs `EUEU` composite order |
| 5 | dissipative generator algebra vs coherent spectral generator algebra |
| 6 | left action `A rho` vs right action `rho A` |

### `Common Operators.png`

Common operators:

```latex
rho in D(H),        rho = 1/2 (I + vec(r) . vec(sigma))

H_0 = 1/2 (n_x sigma_x + n_y sigma_y + n_z sigma_z)

Pi_P(rho) = sum_k P_k rho P_k

F_Q(rho) = (F rho F^dagger) / Tr(F rho F^dagger)

D_-(rho) = sigma_- rho sigma_+ - 1/2 {sigma_+ sigma_-, rho}

D_+(rho) = sigma_+ rho sigma_- - 1/2 {sigma_- sigma_+, rho}

D_P(rho) = sum_j ( P_j rho P_j - 1/2 (P_j rho + rho P_j) )

sigma_pm = 1/2 (sigma_x +- i sigma_y)
```

Bottom heading visible: “Inward Terrains”.

### `Image.png`

Pure visual only: six yin-yang / taijitu variants arranged in two rows. No formula, table, or operator label is visible.

### `Minor  Inner casing.png`

Text: “Yes. Here is the cleaner full chart set.”

Global locks:

| Layer | Type-1 | Type-2 |
|---|---|---|
| Flux | `IN` | `OUT` |
| Major / Outer casing | `WIN / LOSE` | `WIN / LOSE` |
| Minor / Inner casing | `win / lose` | `win / lose` |
| Outer loop family | Deductive `FeTi` | Inductive `TeFi` |
| Inner loop family | Inductive `TeFi` | Deductive `FeTi` |

Loop orders:

| Axis 4 family | Order |
|---|---|
| Inductive | `Se -> Si -> Ni -> Ne` |
| Deductive | `Se -> Ne -> Ni -> Si` |

Terrain graph edges:

| Edge family | Edges |
|---|---|
| `Ax0` | `Se-Si`, `Ne-Ni` |
| `Ax2` | `Se-Ne`, `Si-Ni` |

Loop edge walks:

| Loop | Edge walk |
|---|---|
| Inductive `Se -> Si -> Ni -> Ne` | `Ax0 -> Ax2 -> Ax0 -> Ax2` |
| Deductive `Se -> Ne -> Ni -> Si` | `Ax2 -> Ax0 -> Ax2 -> Ax0` |

### `NeTX.png`

Axis 6 sign:

| Sign | Meaning |
|---|---|
| `UP` | operator first |
| `DOWN` | terrain first |

Type-1 full chart:

| Step | Topology | Terrain | Outer / Major | Ax6 | Signed op | Outer result | Inner / Minor | Ax6 | Signed op | Inner result | Pattern |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `Se` | `Se-in` | `TiSe` | `UP` | `Ti↑` | `LOSE` | `SeFi` | `DOWN` | `Fi↓` | `win` | `LOSEwin` |
| 2 | `Ne` | `Ne-in` | `NeTi` | `DOWN` | `Ti↓` | `WIN` | `FiNe` | `UP` | `Fi↑` | `lose` | `WINlose` |
| 3 | `Ni` | `Ni-in` | `NiFe` | `DOWN` | `Fe↓` | `LOSE` | `TeNi` | `UP` | `Te↑` | `lose` | `loseLOSE` |
| 4 | `Si` | `Si-in` | `FeSi` | `UP` | `Fe↑` | `WIN` | `SiTe` | `DOWN` | `Te↓` | `win` | `winWIN` |

Type-1 loop view:

| Loop | Order | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|
| Outer / Major | Deductive | `Se-in : TiSe : LOSE` | `Ne-in : NeTi : WIN` | `Ni-in : NiFe : LOSE` | `Si-in : FeSi : WIN` |
| Inner / Minor | Inductive | `Se-in : SeFi : win` | `Si-in : SiTe : win` | `Ni-in : TeNi : lose` | `Ne-in : FiNe : lose` |

Type-2 full chart:

| Step | Topology | Terrain | Outer / Major | Ax6 | Signed op | Outer result | Inner / Minor | Ax6 | Signed op | Inner result | Pattern |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `Se` | `Se-out` | `FiSe` | `UP` | `Fi↑` | `WIN` | `SeTi` | `DOWN` | `Ti↓` | `lose` | `loseWIN` |
| 2 | `Si` | `Si-out` | `TeSi` | `UP` | `Te↑` | `WIN` | `SiFe` | `DOWN` | `Fe↓` | `win` | `WINwin` |
| 3 | `Ni` | `Ni-out` | `NiTe` | `DOWN` | `Te↓` | `LOSE` | `FeNi` | `UP` | `Fe↑` | `lose` | `LOSElose` |
| 4 | `Ne` | `Ne-out` | `NeFi` | `DOWN` | `Fi↓` | `LOSE` | `TiNe` | `UP` | `Ti↑` | `win` | `winLOSE` |

The lower Type-2 loop view is cut off.

### `Outer  Malor.png`

Top visible continuation from Type-2 full chart: `Ne`, `Ne-out`, `NeFi`, `DOWN`, `Fi↓`, `LOSE`, `TiNe`, `UP`, `Ti↑`, `win`, `winLOSE`.

Type-2 loop view:

| Loop | Order | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|
| Outer / Major | Inductive | `Se-out : FiSe : WIN` | `Si-out : TeSi : WIN` | `Ni-out : NiTe : LOSE` | `Ne-out : NeFi : LOSE` |
| Inner / Minor | Deductive | `Se-out : SeTi : lose` | `Ne-out : TiNe : win` | `Ni-out : FeNi : lose` | `Si-out : SiFe : win` |

Topology-aligned comparison:

| Topology | Type-1 terrain | Type-1 major | Type-1 minor | Type-2 terrain | Type-2 major | Type-2 minor |
|---|---|---|---|---|---|---|
| `Se` | `Se-in` | `TiSe / LOSE / Ti↑` | `SeFi / win / Fi↓` | `Se-out` | `FiSe / WIN / Fi↑` | `SeTi / lose / Ti↓` |
| `Ne` | `Ne-in` | `NeTi / WIN / Ti↓` | `FiNe / lose / Fi↑` | `Ne-out` | `NeFi / LOSE / Fi↓` | `TiNe / win / Ti↑` |
| `Ni` | `Ni-in` | `NiFe / LOSE / Fe↓` | `TeNi / lose / Te↑` | `Ni-out` | `NiTe / LOSE / Te↓` | `FeNi / lose / Fe↑` |
| `Si` | `Si-in` | `FeSi / WIN / Fe↑` | `SiTe / win / Te↓` | `Si-out` | `TeSi / WIN / Te↑` | `SiFe / win / Fe↓` |

Invariants:

| Engine | `WIN` | `LOSE` | `win` | `lose` |
|---|---:|---:|---:|---:|
| Type-1 | 2 | 2 | 2 | 2 |
| Type-2 | 2 | 2 | 2 | 2 |

| Engine | `↑` stages | `↓` stages |
|---|---|---|
| Type-1 | `Ti↑, Fe↑, Fi↑, Te↑` | `Ti↓, Fe↓, Fi↓, Te↓` |
| Type-2 | `Fi↑, Te↑, Fe↑, Ti↑` | `Ti↓, Fe↓, Te↓, Fi↓` |

### `Pasted Graphic 1.png`

Pure visual only: six small yin-yang / taijitu variants. No formula, table, or operator label is visible.

### `Screenshot 2026-03-28 at 1.25.58 PM.png`

Same visible content as `0. - (o, tio,).png`: carrier table, Pauli matrices, and a cut-off “Nested Hopf Tori” heading.

### `Screenshot 2026-03-28 at 1.26.46 PM.png`

Nested Hopf Tori:

| Object | Formula | Meaning |
|---|---|---|
| torus family | `T_eta = { (e^{i alpha} cos eta, e^{i beta} sin eta) : alpha, beta in S^1 } subset S^3` | nested Hopf-torus family |
| inner loop | `Gamma_inner` | Hopf fiber loop |
| outer loop | `Gamma_outer` | lifted base loop |

Weyl Sheets:

| Engine type | Sheet | Density | Hamiltonian |
|---|---|---|---|
| Type 1 | left Weyl | `rho_L = 1/2 (I + vec(r)_L . vec(sigma))` | `H_L = +H_0` |
| Type 2 | right Weyl | `rho_R = 1/2 (I + vec(r)_R . vec(sigma))` | `H_R = -H_0` |

Shared object:

```latex
H_0 = n_x sigma_x + n_y sigma_y + n_z sigma_z
```

Weyl rotation laws:

```latex
dot(rho)_L = -i[H_L, rho_L]
dot(vec(r))_L = 2 vec(n) x vec(r)_L

dot(rho)_R = -i[H_R, rho_R]
dot(vec(r))_R = -2 vec(n) x vec(r)_R
```

Dissipator:

```latex
D[L](rho) = L rho L^dagger - 1/2 (L^dagger L rho + rho L^dagger L)
```

The Type 1 Terrain Laws heading starts below but is cut.

### `Screenshot 2026-03-28 at 1.27.22 PM.png`

Same visible content as `Outer  Malor.png`: Type-2 loop view, topology-aligned comparison, and invariants.

### `Screenshot 2026-03-28 at 1.27.50 PM.png`

Top cut continuation from “Exact Terrain Pair Separation”:

```latex
Hill / Citadel:
-i[H_S^in, rho_L] + sum_j kappa_j^in (...)
vs
-i[H_S^out, rho_R] + sum_j kappa_j^out (...)
```

Difference: “distinct retained strata on opposite sheets.”

Loop Placement By Engine:

| Engine | Loop | What changes | What stays the same |
|---|---|---|---|
| Type 1 | inner | vector field resolved along Hopf fiber direction | same Type 1 terrain law |
| Type 1 | outer | vector field resolved along lifted-base direction | same Type 1 terrain law |
| Type 2 | inner | vector field resolved along Hopf fiber direction | same Type 2 terrain law |
| Type 2 | outer | vector field resolved along lifted-base direction | same Type 2 terrain law |

Count Table:

| Object | Count | Formula |
|---|---:|---|
| topology families | 4 | `Se, Ne, Ni, Si` |
| terrains per engine | 4 | Type 1: Funnel, Vortex, Pit, Hill; Type 2: Cannon, Spiral, Source, Citadel |
| loop families per engine | 2 | inner, outer |
| stage placements per engine | 8 | `4 x 2` |
| stage placements across both engines | 16 | `4 x 2 x 2` |

Direct Mapping Stack:

| Level | Mathematical object |
|---|---|
| Pauli layer | `I, sigma_x, sigma_y, sigma_z, sigma_pm` |
| spinor layer | `psi in S^3 subset C^2` |
| density layer | `rho = 1/2 (I + vec(r) . vec(sigma))` |
| Weyl layer | `H_L = +H_0, H_R = -H_0` |
| terrain layer | one of the 8 terrain laws above |
| loop layer | inner Hopf fiber or outer lifted-base placement |

### `Screenshot 2026-03-28 at 2.14.07 PM.png`

Definitions / Carrier:

| Label | Exact math |
|---|---|
| left spinor | `psi_L in C^2, ||psi_L|| = 1` |
| right spinor | `psi_R in C^2, ||psi_R|| = 1` |
| carrier manifold | `S^3 = {psi in C^2 : ||psi|| = 1}` |
| left density | `rho_L = psi_L psi_L^dagger = 1/2 (I + vec(r)_L . vec(sigma))` |
| right density | `rho_R = psi_R psi_R^dagger = 1/2 (I + vec(r)_R . vec(sigma))` |
| Hopf coordinates | `psi_s(phi, chi; eta) = ( e^{i(phi+chi)} cos eta, e^{i(phi-chi)} sin eta )^T, s in {L,R}` |
| Hopf projection | `pi(psi) = psi^dagger vec(sigma) psi in S^2` |

Pauli Data:

```latex
vec(sigma) = (sigma_x, sigma_y, sigma_z)
sigma_x = [[0,1],[1,0]]
sigma_y = [[0,-i],[i,0]]
sigma_z = [[1,0],[0,-1]]
sigma_- = [[0,0],[1,0]]
sigma_+ = [[0,1],[0,0]]
```

### `Screenshot 2026-03-28 at 2.14.19 PM.png`

Hamiltonians:

```latex
H_0 = n_x sigma_x + n_y sigma_y + n_z sigma_z
H_L = +H_0
H_R = -H_0
dot(vec(r))_L = 2 vec(n) x vec(r)_L
dot(vec(r))_R = -2 vec(n) x vec(r)_R
```

Dissipative Objects:

```latex
D[L](rho) = L rho L^dagger - 1/2 (L^dagger L rho + rho L^dagger L)

L_k^{F,L} = a_{k0}^{F,L} I + a_{kx}^{F,L} sigma_x + a_{ky}^{F,L} sigma_y + a_{kz}^{F,L} sigma_z
L_k^{C,R} = a_{k0}^{C,R} I + a_{kx}^{C,R} sigma_x + a_{ky}^{C,R} sigma_y + a_{kz}^{C,R} sigma_z
M_k^{V,L} = b_{k0}^{V,L} I + b_{kx}^{V,L} sigma_x + b_{ky}^{V,L} sigma_y + b_{kz}^{V,L} sigma_z
M_k^{S,R} = b_{k0}^{S,R} I + b_{kx}^{S,R} sigma_x + b_{ky}^{S,R} sigma_y + b_{kz}^{S,R} sigma_z

P_j^{H,L} = 1/2 (I + hat(m)_j^{H,L} . vec(sigma)), [K_L, P_j^{H,L}] = 0
P_j^{Ci,R} = 1/2 (I + hat(m)_j^{Ci,R} . vec(sigma)), [K_R, P_j^{Ci,R}] = 0
```

The Loop Geometry heading starts below.

### `Screenshot 2026-03-28 at 2.14.37 PM.png`

Loop Geometry:

```latex
T_eta = { psi_s(phi, chi; eta) : phi, chi in [0, 2pi] } subset S^3

Gamma_f^L(eta, chi_0) = { psi_L(phi, chi_0; eta) : phi in [0, 2pi] }
Gamma_b^L(eta, phi_0) = { psi_L(phi_0 - cos(2 eta) chi, chi; eta) : chi in [0, 2pi] }

Gamma_f^R(eta, chi_0) = { psi_R(phi, chi_0; eta) : phi in [0, 2pi] }
Gamma_b^R(eta, phi_0) = { psi_R(phi_0 - cos(2 eta) chi, chi; eta) : chi in [0, 2pi] }
```

Probe:

```latex
O = O^dagger
p_O(rho) = Tr(O rho)
```

Eight Terrain Laws heading begins. Visible left-sheet rows:

```latex
X_F^L(rho_L) = sum_k D[L_k^{F,L}](rho_L) - i epsilon_{F,L}[H_L, rho_L]
X_V^L(rho_L) = -i[H_L, rho_L] + epsilon_{V,L} sum_k D[M_k^{V,L}](rho_L)
X_P^L(rho_L) = gamma_{P,L} D[sigma_-](rho_L) - i epsilon_{P,L}[H_L, rho_L]
X_H^L(rho_L) = -i[K_L, rho_L] + sum_j kappa_{H,L,j}(P_j^{H,L} rho_L P_j^{H,L} - 1/2(P_j^{H,L} rho_L + rho_L P_j^{H,L}))
```

### `Screenshot 2026-03-28 at 2.14.49 PM.png`

Eight Terrain Laws:

Left sheet / Type 1:

```latex
Se / Funnel:
X_F^L(rho_L) = sum_k D[L_k^{F,L}](rho_L) - i epsilon_{F,L}[H_L, rho_L]

Ne / Vortex:
X_V^L(rho_L) = -i[H_L, rho_L] + epsilon_{V,L} sum_k D[M_k^{V,L}](rho_L)

Ni / Pit:
X_P^L(rho_L) = gamma_{P,L} D[sigma_-](rho_L) - i epsilon_{P,L}[H_L, rho_L]

Si / Hill:
X_H^L(rho_L) = -i[K_L, rho_L] + sum_j kappa_{H,L,j}(P_j^{H,L} rho_L P_j^{H,L} - 1/2(P_j^{H,L} rho_L + rho_L P_j^{H,L}))
```

Right sheet / Type 2:

```latex
Se / Cannon:
X_C^R(rho_R) = sum_k D[L_k^{C,R}](rho_R) - i epsilon_{C,R}[H_R, rho_R]

Ne / Spiral:
X_S^R(rho_R) = -i[H_R, rho_R] + epsilon_{S,R} sum_k D[M_k^{S,R}](rho_R)

Ni / Source:
X_So^R(rho_R) = gamma_{So,R} D[sigma_+](rho_R) - i epsilon_{So,R}[H_R, rho_R]

Si / Citadel:
X_Ci^R(rho_R) = -i[K_R, rho_R] + sum_j kappa_{Ci,R,j}(P_j^{Ci,R} rho_R P_j^{Ci,R} - 1/2(P_j^{Ci,R} rho_R + rho_R P_j^{Ci,R}))
```

The Four Loops heading starts below.

### `Screenshot 2026-03-28 at 2.15.05 PM.png`

Type 1 Terrain Laws:

| Terrain | Topology family | Law on `rho_L` | Pauli realization | Geometric read |
|---|---|---|---|---|
| Funnel | `Se` | `dot(rho)_L = sum_k D[L_k^{Se,in}](rho_L) - i epsilon_{Se,in}[H_L,rho_L]` | `L_k^{Se,in} = a_{k0}^{Se,in} I + vec(a)_k^{Se,in} . vec(sigma)` | inward support transport across nested tori |
| Vortex | `Ne` | `dot(rho)_L = -i[H_L,rho_L] + epsilon_{Ne,in} sum_k D[L_k^{Ne,in}](rho_L)` | Hamiltonian-led circulation with `H_L = + vec(n) . vec(sigma)` | left-handed tangential circulation on fixed Hopf torus |
| Pit | `Ni` | `dot(rho)_L = D[L^{Ni,in}](rho_L) - i epsilon_{Ni,in}[H_L,rho_L]` | `L^{Ni,in} = sqrt(gamma) sigma_-` | contraction from larger torus shells toward inner/core |
| Hill | `Si` | `dot(rho)_L = -i[H_S^in,rho_L] + sum_j kappa_j^in(P_j^in rho_L P_j^in - 1/2(P_j^in rho_L + rho_L P_j^in))` | `P_j^in = 1/2(I + hat(m)_j^in . vec(sigma)), [H_S^in,P_j^in]=0` | retained invariant terraces |

Type 2 Terrain Laws:

| Terrain | Topology family | Law on `rho_R` | Pauli realization | Geometric read |
|---|---|---|---|---|
| Cannon | `Se` | `dot(rho)_R = sum_k D[L_k^{Se,out}](rho_R) - i epsilon_{Se,out}[H_R,rho_R]` | `L_k^{Se,out} = a_{k0}^{Se,out} I + vec(a)_k^{Se,out} . vec(sigma)` | outward support transport across nested tori |
| Spiral | `Ne` | `dot(rho)_R = -i[H_R,rho_R] + epsilon_{Ne,out} sum_k D[L_k^{Ne,out}](rho_R)` | Hamiltonian-led circulation with `H_R = - vec(n) . vec(sigma)` | right-handed tangential circulation on fixed Hopf torus |
| Source | `Ni` | `dot(rho)_R = D[L^{Ni,out}](rho_R) - i epsilon_{Ni,out}[H_R,rho_R]` | `L^{Ni,out} = sqrt(gamma) sigma_+` | emission from inner/core torus region outward |
| Citadel | `Si` | `dot(rho)_R = -i[H_S^out,rho_R] + sum_j kappa_j^out(P_j^out rho_R P_j^out - 1/2(P_j^out rho_R + rho_R P_j^out))` | `P_j^out = 1/2(I + hat(m)_j^out . vec(sigma)), [H_S^out,P_j^out]=0` | retained outward strata on opposite sheet |

Exact Terrain Pair Separation:

| Pair | Type 1 law | Type 2 law | Actual mathematical difference |
|---|---|---|---|
| Funnel / Cannon | `sum_k D[L_k^{Se,in}](rho_L) - i epsilon_{Se,in}[H_L,rho_L]` | `sum_k D[L_k^{Se,out}](rho_R) - i epsilon_{Se,out}[H_R,rho_R]` | opposite Weyl sign and distinct dissipative family |
| Vortex / Spiral | `-i[H_L,rho_L] + epsilon_{Ne,in} sum_k D[L_k^{Ne,in}](rho_L)` | `-i[H_R,rho_R] + epsilon_{Ne,out} sum_k D[L_k^{Ne,out}](rho_R)` | opposite Hopf circulation handedness |
| Pit / Source | `D[sqrt(gamma) sigma_-](rho_L) - i epsilon_{Ni,in}[H_L,rho_L]` | `D[sqrt(gamma) sigma_+](rho_R) - i epsilon_{Ni,out}[H_R,rho_R]` | sink vs source |
| Hill / Citadel | projector-retention form | projector-retention form | distinct retained strata on opposite sheets |

Loop Placement By Engine begins below.

### `Screenshot 2026-03-28 at 2.15.21 PM.png`

Text:

- “So for Type 1:”
- outer = deductive
- inner = inductive

Table:

| Step | Outer deductive terrain | Outer pair | Ax6 | Outer result | Inner inductive terrain | Inner pair | Ax6 | Inner result |
|---|---|---|---|---|---|---|---|---|
| 1 | `Se-in` | `TiSe` | `UP` | `LOSE` | `Se-in` | `SeFi` | `DOWN` | `win` |
| 2 | `Ne-in` | `NeTi` | `DOWN` | `WIN` | `Si-in` | `SiTe` | `DOWN` | `win` |
| 3 | `Ni-in` | `NiFe` | `DOWN` | `LOSE` | `Ni-in` | `TeNi` | `UP` | `lose` |
| 4 | `Si-in` | `FeSi` | `UP` | `WIN` | `Ne-in` | `FiNe` | `UP` | `lose` |

Text: “So the clean separation is:”

Partial table visible:

| Layer | Meaning |
|---|---|
| Engine type | chooses `in` vs `out` terrain family |

Remaining rows are cut off.

### `Screenshot 2026-03-28 at 2.15.31 PM.png`

Full 16 Placements:

| # | Label | Exact placement |
|---:|---|---|
| 1 | `Se / Funnel on Type 1 inner` | `(X_F^L, Gamma_f^L)` |
| 2 | `Ne / Vortex on Type 1 inner` | `(X_V^L, Gamma_f^L)` |
| 3 | `Ni / Pit on Type 1 inner` | `(X_P^L, Gamma_f^L)` |
| 4 | `Si / Hill on Type 1 inner` | `(X_H^L, Gamma_f^L)` |
| 5 | `Se / Funnel on Type 1 outer` | `(X_F^L, Gamma_b^L)` |
| 6 | `Ne / Vortex on Type 1 outer` | `(X_V^L, Gamma_b^L)` |
| 7 | `Ni / Pit on Type 1 outer` | `(X_P^L, Gamma_b^L)` |
| 8 | `Si / Hill on Type 1 outer` | `(X_H^L, Gamma_b^L)` |
| 9 | `Se / Cannon on Type 2 inner` | `(X_C^R, Gamma_f^R)` |
| 10 | `Ne / Spiral on Type 2 inner` | `(X_S^R, Gamma_f^R)` |
| 11 | `Ni / Source on Type 2 inner` | `(X_So^R, Gamma_f^R)` |
| 12 | `Si / Citadel on Type 2 inner` | `(X_Ci^R, Gamma_f^R)` |
| 13 | `Se / Cannon on Type 2 outer` | `(X_C^R, Gamma_b^R)` |
| 14 | `Ne / Spiral on Type 2 outer` | `(X_S^R, Gamma_b^R)` |
| 15 | `Ni / Source on Type 2 outer` | `(X_So^R, Gamma_b^R)` |
| 16 | `Si / Citadel on Type 2 outer` | `(X_Ci^R, Gamma_b^R)` |

Count:

| Label | Count |
|---|---:|
| loops | 4 |
| stages per loop | 4 |
| placements | 16 |

### `Sim shape.png`

Sim shape:

```latex
Phi_substage

Phi_stage = Phi_substage,4 o Phi_substage,3 o Phi_substage,2 o Phi_substage,1

Phi_loop = Phi_stage,4 o Phi_stage,3 o Phi_stage,2 o Phi_stage,1

Phi_engine = Phi_outer loop o Phi_inner loop
or the reverse, if the schedule specifies that

Phi_schedule = Phi_engine,N o ... o Phi_engine,1
```

Text above: “You are also right that the sim must be tiered. The non-toy version is:”

Text below is cut off.

### `Terrain.png`

Type 1:

| Topology | Terrain | Major / Outer | Axis 6 | Ordered operator | Result | Minor / Inner | Axis 6 | Ordered operator | Result | Pattern |
|---|---|---|---|---|---|---|---|---|---|---|
| `Ne` | `Ne-in` | `NeTi` | `DOWN` | `Ti↓` | `WIN` | `FiNe` | `UP` | `Fi↑` | `lose` | `WINlose` |
| `Si` | `Si-in` | `FeSi` | `UP` | `Fe↑` | `WIN` | `SiTe` | `DOWN` | `Te↓` | `win` | `winWIN` |
| `Se` | `Se-in` | `TiSe` | `UP` | `Ti↑` | `LOSE` | `SeFi` | `DOWN` | `Fi↓` | `win` | `LOSEwin` |
| `Ni` | `Ni-in` | `NiFe` | `DOWN` | `Fe↓` | `LOSE` | `TeNi` | `UP` | `Te↑` | `lose` | `loseLOSE` |

Type 2:

| Topology | Terrain | Major / Outer | Axis 6 | Ordered operator | Result | Minor / Inner | Axis 6 | Ordered operator | Result | Pattern |
|---|---|---|---|---|---|---|---|---|---|---|
| `Ne` | `Ne-out` | `NeFi` | `DOWN` | `Fi↓` | `LOSE` | `TiNe` | `UP` | `Ti↑` | `win` | `winLOSE` |
| `Si` | `Si-out` | `TeSi` | `UP` | `Te↑` | `WIN` | `SiFe` | `DOWN` | `Fe↓` | `win` | `WINwin` |
| `Se` | `Se-out` | `FiSe` | `UP` | `Fi↑` | `WIN` | `SeTi` | `DOWN` | `Ti↓` | `lose` | `loseWIN` |
| `Ni` | `Ni-out` | `NiTe` | `DOWN` | `Te↓` | `LOSE` | `FeNi` | `UP` | `Fe↑` | `lose` | `LOSElose` |

Text below starts: “So the comparison result is:” and is cut off.

### `The actuel candidene math we've been ceeling la lunt thit, once, in one table.png`

Same table family as `Topology.png`, with the top of the global locks visible only in part. Visible Type-2 global-lock row: `Type-2 | OUT | Inductive TeFi | Deductive FeTi`.

Then Type-1 Full Chart and Type-2 Full Chart match `Topology.png`.

### `Topology.png`

Type-1 Full Chart:

| Step | Topology | Terrain | Loop | Order family | Stage token | Axis 6 | Signed operator | Result | Pattern |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | `Se` | `Se-in` | Outer / Major | Deductive | `TiSe` | `UP` | `Ti↑` | `LOSE` | `LOSEwin` |
| 2 | `Ne` | `Ne-in` | Outer / Major | Deductive | `NeTi` | `DOWN` | `Ti↓` | `WIN` | `WINlose` |
| 3 | `Ni` | `Ni-in` | Outer / Major | Deductive | `NiFe` | `DOWN` | `Fe↓` | `LOSE` | `loseLOSE` |
| 4 | `Si` | `Si-in` | Outer / Major | Deductive | `FeSi` | `UP` | `Fe↑` | `WIN` | `winWIN` |
| 1 | `Se` | `Se-in` | Inner / Minor | Inductive | `SeFi` | `DOWN` | `Fi↓` | `win` | `LOSEwin` |
| 2 | `Si` | `Si-in` | Inner / Minor | Inductive | `SiTe` | `DOWN` | `Te↓` | `win` | `winWIN` |
| 3 | `Ni` | `Ni-in` | Inner / Minor | Inductive | `TeNi` | `UP` | `Te↑` | `lose` | `loseLOSE` |
| 4 | `Ne` | `Ne-in` | Inner / Minor | Inductive | `FiNe` | `UP` | `Fi↑` | `lose` | `WINlose` |

Type-2 Full Chart:

| Step | Topology | Terrain | Loop | Order family | Stage token | Axis 6 | Signed operator | Result | Pattern |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | `Se` | `Se-out` | Outer / Major | Inductive | `FiSe` | `UP` | `Fi↑` | `WIN` | `loseWIN` |
| 2 | `Si` | `Si-out` | Outer / Major | Inductive | `TeSi` | `UP` | `Te↑` | `WIN` | `WINwin` |
| 3 | `Ni` | `Ni-out` | Outer / Major | Inductive | `NiTe` | `DOWN` | `Te↓` | `LOSE` | `LOSElose` |
| 4 | `Ne` | `Ne-out` | Outer / Major | Inductive | `NeFi` | `DOWN` | `Fi↓` | `LOSE` | `winLOSE` |
| 1 | `Se` | `Se-out` | Inner / Minor | Deductive | `SeTi` | `DOWN` | `Ti↓` | `lose` | `loseWIN` |
| 2 | `Ne` | `Ne-out` | Inner / Minor | Deductive | `TiNe` | `UP` | `Ti↑` | `win` | `winLOSE` |
| 3 | `Ni` | `Ni-out` | Inner / Minor | Deductive | `FeNi` | `UP` | `Fe↑` | `lose` | `LOSElose` |
| 4 | `Si` | `Si-out` | Inner / Minor | Deductive | `SiFe` | `DOWN` | `Fe↓` | `win` | `WINwin` |

Bottom heading visible: “Topology-Aligned Comparison”.

### `Yin and yang.png`

Visual/source image, not a math table. Transcribed visible labels:

- “Yin and yang”
- “Philosophical concept of dualism in Chinese philosophy, traditional medicine, fengshui, and protoscience, opposing solar/masculine/active/warm yang with lunar/feminine/passive/cool yin.”
- Highlighted text: “Yin and yang, also yinyang or yin-yang, is a concept that originated in Chinese philosophy, describing an opposite but interconnected, self-perpetuating cycle. Wikipedia”

Diagram labels:

- “Information flux on the Topology of the Torus”
- “Integration, coupling, enfolding, superposition, entanglement, reflection”
- “Gravity”
- “Inner Core”
- “Spiral Information Trajectory”
- “Event Horizon”
- “Dark Energy”
- “Neg-entropic, Converging Halve”
- “Entropic, Diversion Halve”
- “Entropic information generation / compression, unfolding”

No operator formula is visible.

### `it Hand oft.png`

Text:

- “So the axes do not replace the geometry.”
- “They act on the state/process layer living on that geometry.”

Axis 0 on the manifold:

```latex
phi_0(x) = Phi_0(rho(x))

Phi_0(rho) = sum_r w_r I_c(A_r > B_r)_rho = - sum_r w_r S(A_r | B_r)_rho
```

The symbol in `I_c(A_r > B_r)` appears to be the coherent-information ket-side notation, likely `I_c(A_r \rangle B_r)_rho`; the screenshot is visually ambiguous.

This means:

- `Axis 0` acts on the manifold through the state attached to each point.
- it is not an engine operator.
- it grades trajectories on the nested Hopf/Weyl geometry.

Important caveat:

- “A single isolated Weyl spinor is not enough for conditional entropy.”
- “Conditional entropy needs a bipartite state:”

```latex
rho_AB
```

For Axis 0 usually need:

- a coupled left/right state `rho_{LR}`
- or a shell-cut bipartition `rho_{A_r B_r}`
- or a reduced multipartite state derived from the manifold point

Strict pipeline:

```latex
x in M -> (psi_L(x), psi_R(x)) -> rho_LR(x) or rho_{A_r B_r}(x) -> Phi_0(rho(x))
```

Bottom line visible:

- “Yes, this operates on the geometric constraints.”
- “But the clean alignment is:” then cut off.

## 2. Operator Menu Delta

Current baseline checked in `operator math explicit.md`: the current intrinsic operator math is only these four base operators:

| Current token | Current operator meaning |
|---|---|
| `Ti` | `D_z` dephase, dephasing in the `sigma_z` eigenbasis |
| `Te` | `D_x` dephase, dephasing in the `sigma_x` eigenbasis |
| `Fi` | `R_x`, unitary rotation about `sigma_x` |
| `Fe` | `R_z`, unitary rotation about `sigma_z` |

The screenshots contain the token names `Ti`, `Te`, `Fi`, and `Fe` in table stage tokens and signed operators. They do not contain the current exact four formulas for `Ti`, `Te`, `Fi`, and `Fe` as written in `operator math explicit.md`.

### Screenshot operators absent from the current four-operator set

These appear in the 26 screenshots but are absent from the current intrinsic set `{D_z, D_x, R_x, R_z}`:

| Screenshot object | Where it appears | Delta against current set |
|---|---|---|
| Arbitrary 3-axis Hamiltonian `H_0 = n_x sigma_x + n_y sigma_y + n_z sigma_z` and variant `H_0 = 1/2(...)` | `1(0)...png`, `Common Operators.png`, `Screenshot 2026-03-28 at 1.26.46 PM.png`, `2.14.19 PM.png` | Current set has only x- and z-axis rotations, no arbitrary-axis Hamiltonian family and no current `R_y`. |
| `sigma_y` as a first-class Pauli basis component | carrier, Pauli, Hamiltonian, and raising/lowering images | Current doc defines `sigma_y` as a fixed matrix but has no y-axis dephase/rotation operator in the four-token packet. |
| `Pi_P(rho) = sum_k P_k rho P_k` | `Common Operators.png` | Projective channel absent from current four-token set. |
| `F_Q(rho) = F rho F^dagger / Tr(F rho F^dagger)` | `Common Operators.png`, inward/outward terrain law screenshots | Normalized filter / POVM-like update absent from current four-token set. |
| `D_-(rho)` / `D_+(rho)` | `Common Operators.png`; Pit/Source laws | Amplitude lowering/raising dissipators absent from current four-token set. |
| `D_P(rho)` | `Common Operators.png`, Hill/Citadel laws | Projector dephasing/retention channel absent from current four-token set as a named menu item. |
| Generic Lindblad `D[L](rho)` | `Screenshot 2026-03-28 at 1.26.46 PM.png`, `2.14.19 PM.png`, `2.14.49 PM.png`, `2.15.05 PM.png` | Current four-token set has only two dephases and two rotations, not a generic GKSL menu. |
| General Pauli-expanded `L_k` and `M_k` operator families | `2.14.19 PM.png`, `2.14.49 PM.png`, `2.15.05 PM.png` | More general dissipative families than current four-token packet. |
| Projectors `P_j = 1/2(I + hat(m)_j . vec(sigma))` with commutation constraints | `2.14.19 PM.png`, `2.15.05 PM.png` | General projective-instrument/retention family absent from current four-token packet. |
| Observable probe `O=O^dagger`, `p_O(rho)=Tr(O rho)` | `2.14.37 PM.png` | Probe/readout layer, not a current engine operator. |
| Axis 0 functional `Phi_0(rho)` / coherent information / conditional entropy | `it Hand oft.png` | Not an engine operator; current Axis 0 QIT docs keep it as a cut-state scalar family, not part of the four operator set. |

### Current operators absent from screenshots

Checked against all 26 images:

- The labels `Ti`, `Te`, `Fi`, `Fe` are present in the screenshots.
- The current exact formulas for `Ti = D_z` using `P_0, P_1`, `Te = D_x` using `Q_+, Q_-`, `Fi = R_x` using `U_x(theta)`, and `Fe = R_z` using `U_z(phi)` are not written in the screenshots.
- The current doc’s exact `P_0/P_1` and `Q_+/Q_-` bases are not visible in these 26 images. Related but not identical generic projectors `P_j` are visible.

### The y-axis question

Checked all 26 images and `operator math explicit.md`:

- `sigma_y` appears repeatedly in screenshots as part of `vec(sigma)=(sigma_x,sigma_y,sigma_z)`, as the explicit Pauli matrix, inside `H_0`, and inside `sigma_pm = 1/2(sigma_x +- i sigma_y)`.
- `sigma_y` also appears in the current operator document as a fixed matrix.
- No screenshot defines a named `D_y` or `R_y`.
- The current four-operator set has no y-axis operator: no `D_y` dephase and no `R_y` rotation. So the screenshots use y as part of the full Pauli carrier and generic Hamiltonian/operator basis, while the current operational token menu projects down to x/z only.

## 3. Spectral vs Gradient

Images checked: all 26 screenshots. Repo text checked: `system_v4/probes/` and `system_v5/READ ONLY Reference Docs/`.

### Screenshot occurrences

The only visible screenshot occurrence of this distinction is in `Can it operate directly on leftjright Weyt spinors.png`:

```text
Axis 5: dissipative generator algebra vs coherent spectral generator algebra
```

No visible screenshot defines “finite spectral algebra” or “finite gradient algebra” as exact phrases. No visible screenshot defines “gradient algebra” directly.

### Repo drift search findings

`system_v4/probes/` search found spectral and gradient language, but not the exact phrase pair “finite spectral algebra” / “finite gradient algebra.”

Relevant drift examples:

- `type2_engine_sim.py` has `Fi: spectral filter matrix (Kraus-like)`.
- `sim_GA5_coupling_strength.py` describes `Fi` as a “projective/spectral filter.”
- `qit_complete_math_reference.py` says `Fi = spectral filter -> quasi-measurement (ambiguous)`.
- `engine_math_contract.py` has older/drifted labels: `Te (unitary rotation), Fi (spectral filter)`, which conflicts with the current operator doc.
- Many probes use `Axis 0 gradient`, `entropy gradient`, `autograd gradient`, or `dQ/d(eps)` for differentiable evidence, especially dephasing/MI and FEP-style probes.
- Hot/cold probes appear as Carnot labels such as `hot_isotherm` and `cold_isotherm`.
- Wave probes appear as older `H_wave = log(2)` shell/speed constraints.

`system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md` contains the clearest older written spectral/gradient split:

```text
Axis 5: dissipative generator algebra vs coherent spectral generator algebra
Hamiltonian / gradient flow: rho -> U rho U^dagger, dot(rho)=-i[H,rho]
spectral projection / mode filter: rho -> F rho F^dagger / Tr(F rho F^dagger)
dissipative / finite-gradient side: GKSL / Lindblad / semigroup
coherent spectral side: Hamiltonian / projector-spectral / group
```

### Does spectral/gradient map to dephasing vs rotation?

Not cleanly.

- Current map: `Ti,Te` are dephasing and `Fi,Fe` are rotations.
- Screenshot/older-doc map: “dissipative generator algebra vs coherent spectral generator algebra” is broader than dephasing-vs-rotation. It includes Lindblad/GKSL dissipation, Hamiltonian coherent flow, projectors, spectral filters, and possibly group/spectrum structure.
- Drifted probe/doc language sometimes maps `Fi` to a spectral filter, but current `operator math explicit.md` supersedes that with `Fi = R_x`.

So the faithful answer is: the dated candidate material points to a broader Axis 5 generator-algebra split; the current set compresses the operational menu to dephasing-vs-rotation over four tokens.

## 4. Dichotomy Audit

### Requested dichotomies

| Dichotomy | Found in 26 images? | What was checked | Current-math counterpart |
|---|---|---|---|
| line vs wave | No direct definition visible | All 26 images; `system_v4/probes/` search for `line`, `wave`, `H_wave`; current docs search | Older probes have `H_wave = log(2)` wave labels and legacy docs have line/wave metaphors. No current four-operator counterpart. |
| hot vs cold | No direct math definition visible in screenshots | All 26 images; `system_v4/probes/` search for `hot_isotherm`, `cold_isotherm`; current docs search for `hot`, `cool` | `Yin and yang.png` has warm/cool symbolic text. Current docs treat hot/cool as symbolic Axis 5 / heating-cooling metaphor and probes contain Carnot hot/cold isotherms. No exact current operator counterpart. |

### Dichotomies actually carried by the screenshot tables

| Dichotomy in screenshots | Screenshot evidence | Best current counterpart | Status |
|---|---|---|---|
| Type-1 / Type-2 | tables, Weyl sheets | left/right Weyl sheet; Flux `IN/OUT` in older terrain packet | Keep as candidate/provenance; current docs may compile parts but not all tables. |
| `IN` / `OUT` | global locks, terrain labels `Se-in`, `Se-out` | `Flux2` / in-out terrain family | Current symbolic/current-map counterpart exists. |
| left / right | `rho_L`, `rho_R`, `H_L`, `H_R` | Weyl chirality sheet | Current QIT docs keep this as screenshot-backed working layer, not source theorem. |
| inner / outer | Hopf fiber vs lifted-base loops, Type loop tables | Axis 3 placement: fiber vs lifted-base loop class | Strong current counterpart. |
| major / minor | “Major / Outer casing” vs “Minor / Inner casing” | Mostly outer/inner loop placement and result casing | No independent current operator counterpart beyond table/casing convention. |
| deductive / inductive | `FeTi` vs `TeFi`, loop orders | Axis 4 order family | Current counterpart exists as order-family layer. |
| `UP` / `DOWN` | Axis 6 sign table | Axis 6 precedence/order: operator first vs terrain first | Current counterpart exists. |
| `WIN/LOSE` vs `win/lose` | stage result casing | Axis 0 response/result token layer | Candidate/result-table convention; not itself an operator. |
| dissipative vs coherent spectral | Axis 5 row | Axis 5 operator/generator family | Current counterpart is narrower: dephasing-family vs rotation-family. |
| `sigma_-` vs `sigma_+` | Pit/Source laws | amplitude lowering vs raising | Genuinely absent from current four-token operator set. |
| sink vs source | Pit/Source pair separation | amplitude lowering/raising; inward/outward flow | Candidate, not in current four-token operator set. |
| projector vs Fourier/filter | Inward/outward terrain law table | projective channel vs normalized filter | Candidate, absent from current four-token operator set. |
| yin / yang | `Yin and yang.png`, taijitu visuals | symbolic overlay only | No exact current operator counterpart. |
| entropic / neg-entropic halves | `Yin and yang.png` external diagram | Axis 0 response / entropy metaphor | No exact current operator counterpart from screenshots alone. |

## 5. ASSISTANT-ANALYSIS: Completeness Frame

This section is analysis, not screenshot transcription. It answers the owner’s “all possible operators” concern as a single-qubit channel-menu checklist.

| Single-qubit channel/menu cell | Covered by screenshots? | Covered by current 4-operator set? | Notes |
|---|---|---|---|
| Unitary rotation about x, `R_x` | Token-level only: `Fi` appears; no `U_x` formula | Yes, `Fi = R_x` | Current doc is clearer than screenshots. |
| Unitary rotation about y, `R_y` | Generic `H_0` includes `sigma_y`, but no named `R_y` | No | Gap in current four-token set. |
| Unitary rotation about z, `R_z` | Token-level only: `Fe` appears; no `U_z` formula | Yes, `Fe = R_z` | Current doc is clearer than screenshots. |
| Arbitrary-axis Hamiltonian `n . sigma` | Yes | No, except x/z special cases | Screenshot candidate is broader. |
| Dephasing about z, `D_z` | Token-level only: `Ti`; generic projectors visible | Yes, `Ti = D_z` | Current doc is clearer. |
| Dephasing about x, `D_x` | Token-level only: `Te`; generic projectors visible | Yes, `Te = D_x` | Current doc is clearer. |
| Dephasing about y, `D_y` | No named `D_y`; generic `D_P` can imply arbitrary projectors | No | Gap if full Pauli-axis menu is desired. |
| Amplitude lowering / damping, `D_-` | Yes: `D_-`, `D[sigma_-]`, Pit | No | Screenshot-only candidate. |
| Amplitude raising / excitation, `D_+` | Yes: `D_+`, `D[sigma_+]`, Source | No | Screenshot-only candidate. |
| Depolarizing channel | No explicit depolarizing formula found | No | Neither set covers it in checked materials. |
| Projective instrument/channel `Pi_P` | Yes | No | Screenshot-only candidate. |
| Projector dephasing/retention `D_P` | Yes | No as named operator | Screenshot-only candidate; current `Ti/Te` are special dephases, not generic `D_P`. |
| Normalized filter / POVM update `F_Q` | Yes | No | Screenshot-only candidate. |
| General GKSL / Lindblad family `D[L]` | Yes | No, except specific dephasing generators in current doc | Screenshot candidate is broader. |
| Observable probe/readout `Tr(O rho)` | Yes | No | Probe layer, not necessarily engine operator. |
| Cut-state scalar `Phi_0`, coherent information | Yes | No | Axis 0 scalar/readout layer, not engine operator. |

Bottom line: the screenshots cover a broader but dated candidate operator menu. The current four-token set covers a deliberately small x/z dephase-and-rotate packet. Neither set, as checked, covers the full single-qubit channel menu.

## 6. Verdict Table

| Image | Verdict | Reason |
|---|---|---|
| `0. - (o, tio,).png` | KEEP-AS-FUEL | Useful carrier/Pauli inventory; density row is garbled; no promotion. |
| `1(0) -1021 - 3(1 +7-0).png` | KEEP-AS-FUEL | Clean Hopf/Weyl carrier formulas and `sigma_y` evidence; superseded operationally by current operator doc for four-token engine math. |
| `Can it operate directly on leftjright Weyt spinors.png` | KEEP-AS-FUEL | Contains the key dated Axis 5 spectral/dissipative language and axis-role table; current docs narrow the operator set. |
| `Common Operators.png` | GENUINELY-NEW-CANDIDATE | Contains operator menu items absent from current four-token set: `Pi_P`, `F_Q`, `D_-`, `D_+`, `D_P`, arbitrary `H_0`. Candidate only. |
| `Image.png` | KEEP-AS-FUEL | Visual taijitu variants only; no math definition. |
| `Minor  Inner casing.png` | SUPERSEDED-BY current axis docs | Global-lock/loop-order chart matches older terrain-map conventions; useful provenance but not a current proof. |
| `NeTX.png` | SUPERSEDED-BY current axis docs | Stage-token tables and Axis 6 sign are provenance for current Axis 6/order maps. |
| `Outer  Malor.png` | SUPERSEDED-BY current axis docs | Topology-aligned comparison and invariants are table provenance, not operator definitions. |
| `Pasted Graphic 1.png` | KEEP-AS-FUEL | Visual taijitu variants only. |
| `Screenshot 2026-03-28 at 1.25.58 PM.png` | KEEP-AS-FUEL | Carrier/Pauli inventory duplicate; density row garbled. |
| `Screenshot 2026-03-28 at 1.26.46 PM.png` | KEEP-AS-FUEL | Hopf/Weyl carrier and dissipator formulas; includes arbitrary `H_0`. |
| `Screenshot 2026-03-28 at 1.27.22 PM.png` | SUPERSEDED-BY current axis docs | Type-2 loop view, topology comparison, and invariants are older table provenance. |
| `Screenshot 2026-03-28 at 1.27.50 PM.png` | KEEP-AS-FUEL | Loop-placement/count/direct stack is useful provenance; not a current operator menu. |
| `Screenshot 2026-03-28 at 2.14.07 PM.png` | KEEP-AS-FUEL | Strong carrier/Hopf/Pauli transcription; useful for y-axis and spinor layer. |
| `Screenshot 2026-03-28 at 2.14.19 PM.png` | GENUINELY-NEW-CANDIDATE | Generic dissipative families and projectors exceed current four-token operator set. |
| `Screenshot 2026-03-28 at 2.14.37 PM.png` | GENUINELY-NEW-CANDIDATE | Loop geometry plus observable probe/readout and terrain-law starts; probe layer absent from current operator set. |
| `Screenshot 2026-03-28 at 2.14.49 PM.png` | GENUINELY-NEW-CANDIDATE | Eight terrain laws include generic Lindblad, amplitude raise/lower, and projector families beyond current four operators. |
| `Screenshot 2026-03-28 at 2.15.05 PM.png` | GENUINELY-NEW-CANDIDATE | Detailed terrain laws and pair separations preserve operator families absent from current set; candidate only. |
| `Screenshot 2026-03-28 at 2.15.21 PM.png` | SUPERSEDED-BY current axis docs | Type-1 separation table is older route/table convention. |
| `Screenshot 2026-03-28 at 2.15.31 PM.png` | KEEP-AS-FUEL | Full 16 placements are useful as dated placement inventory; not an operator expansion by itself. |
| `Sim shape.png` | KEEP-AS-FUEL | Tiered channel-composition shape is useful sim design fuel; not current operator-set evidence. |
| `Terrain.png` | SUPERSEDED-BY current axis docs | Older Type1/Type2 comparison table; useful for provenance only. |
| `The actuel candidene math we've been ceeling la lunt thit, once, in one table.png` | SUPERSEDED-BY current axis docs | Duplicate/variant of current table-provenance material. |
| `Topology.png` | SUPERSEDED-BY current axis docs | Stage-token full charts are older table conventions; current operator doc controls token meanings. |
| `Yin and yang.png` | KEEP-AS-FUEL | Symbolic/metaphor reference for yin/yang, warm/cool, entropic/neg-entropic halves; no current math promotion. |
| `it Hand oft.png` | SUPERSEDED-BY `AXIS_0_1_2_QIT_MATH.md` | Axis 0 cut-state/coherent-information shape is already carried as screenshot-backed candidate in current Axis 0 docs. |

## Bottom-Line Delta

The screenshots are not “all possible operators.” They are a dated, broader candidate packet containing:

- the current token names `Ti`, `Te`, `Fi`, `Fe`;
- a wider Pauli/Hopf/Weyl carrier layer with `sigma_y`;
- generic Lindblad/projector/filter/amplitude operators not present in the current four-token set;
- symbolic/terrain dichotomies that current docs partly compress into Axis 0, Axis 3, Axis 4, Axis 5, Axis 6, and Flux2.

The strongest actionable delta is not to replace the current four operators. It is to preserve a candidate backlog of missing single-qubit channel families: arbitrary-axis Hamiltonian including y, y-axis dephase/rotation, amplitude raise/lower, projector channels, normalized filters/POVMs, generic GKSL families, and probe/readout operators.
