# Terrain Generator Source Layout

**Created:** 2026-05-22
**Status:** source-grounded terrain correction; no runtime promotion

## Purpose

This packet restores the terrain math that was flattened in the previous
axis/operator layouts.

Main correction:

```text
There are two different 16-count objects.

1. 16 ordered tokens:
   topology x operator family x precedence

2. 16 terrain placements:
   8 terrain generator laws x 2 loop placements
```

These are not the same layer.

The previous row-matrix overfocused on ordered tokens and underrepresented the
terrain generator laws. This packet corrects that.

## Source Anchors

Primary terrain sources read:

```text
READ ONLY Reference Docs/terrain math.md
READ ONLY Reference Docs/terrains.md
READ ONLY Reference Docs/apple axes terrain operator math.md
READ ONLY Reference Docs/JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP copy.md
READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md
```

Strong anchors:

| Source object | Lines |
|---|---|
| terrain spinor / density / Bloch variables | `terrain math.md` lines 3-13 |
| loop geometry and vector fields | `terrain math.md` lines 26-49 |
| sheet Hamiltonians and Bloch sheet flows | `terrain math.md` lines 51-64 |
| dissipator definition | `terrain math.md` lines 66-70 |
| eight terrain generators | `terrain math.md` lines 72-83 |
| Type 1 / Type 2 terrain placements | `terrain math.md` lines 92-137 |
| explicit separation of 4 families / 8 terrains / 16 placements | `terrain math.md` lines 139-152 |
| left/right terrain laws | `terrains.md` lines 59-75 |
| four loop objects | `terrains.md` lines 77-91 |
| full 16 placements | `terrains.md` lines 129-148 |

## Carrier State Variables

The terrain layer lives on the spinor and density manifold:

```text
psi_s(phi, chi; eta)
= [ exp(i(phi + chi)) cos eta,
    exp(i(phi - chi)) sin eta ]^T

s in {L,R}
phi, chi in [0,2pi)
eta in [0,pi/2]
```

Carrier:

```text
S_s^3 = { psi_s in C^2 : ||psi_s|| = 1 }
```

Density:

```text
rho_s = psi_s psi_s^dagger
```

Explicit density matrix:

```text
rho_s(phi,chi;eta) =
[[cos^2 eta,                         exp(2 i chi) cos eta sin eta],
 [exp(-2 i chi) cos eta sin eta,     sin^2 eta]]
```

Bloch form:

```text
rho_s = 1/2(I + r_x sigma_x + r_y sigma_y + r_z sigma_z)
```

Bloch vector:

```text
r_s(phi,chi;eta)
= (sin(2 eta) cos(2 chi),
   sin(2 eta) sin(2 chi),
   cos(2 eta))
```

This is the terrain carrier. Terrain laws act on `rho_s`; loop laws constrain
how `psi_s` moves in `S^3`.

## Loop Geometry

Torus family:

```text
T_eta^s = { psi_s(phi,chi;eta) : phi,chi in [0,2pi) } subset S_s^3
```

Hopf connection:

```text
A = -i psi_s^dagger d psi_s
  = d phi + cos(2 eta) d chi
```

Two loop paths:

```text
inner/fiber:
  gamma_in^s(u) = psi_s(phi_0 + u, chi_0; eta_0)

outer/lifted-base:
  gamma_out^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)
```

Horizontal condition:

```text
A(dot gamma_out^s) = 0
```

Loop vector fields:

```text
Y_in psi_s = partial_phi psi_s
           = i [ exp(i(phi+chi)) cos eta,
                 exp(i(phi-chi)) sin eta ]^T
```

```text
Y_out psi_s = (-cos(2 eta) partial_phi + partial_chi) psi_s
            = i [ (1 - cos 2eta) exp(i(phi+chi)) cos eta,
                 -(1 + cos 2eta) exp(i(phi-chi)) sin eta ]^T
```

Density visibility:

```text
rho_in^s(u) = rho_s(phi_0 + u, chi_0; eta_0)
            = rho_s(phi_0, chi_0; eta_0)
```

so inner/fiber motion is density-stationary.

```text
rho_out^s(u) = rho_s(phi_0 - cos(2 eta_0)u, chi_0 + u; eta_0)
```

with:

```text
rho_out^s(u) =
[[cos^2 eta_0,                         exp(2 i (chi_0+u)) cos eta_0 sin eta_0],
 [exp(-2 i (chi_0+u)) cos eta_0 sin eta_0, sin^2 eta_0]]
```

so outer/lifted-base motion is density-visible.

## Sheet Hamiltonians

Base Hamiltonian:

```text
H_0 = n_x sigma_x + n_y sigma_y + n_z sigma_z
```

Sheet Hamiltonians:

```text
H_L = +H_0
H_R = -H_0
```

Sheet flows:

```text
dot rho_L = -i[H_L, rho_L]
dot r_L   =  2 n x r_L
```

```text
dot rho_R = -i[H_R, rho_R]
dot r_R   = -2 n x r_R
```

This sheet sign is terrain-relevant. It is not an optional narrative label.

## Dissipator

Terrain dissipators use:

```text
D[L](rho) = L rho L^dagger
          - 1/2 (L^dagger L rho + rho L^dagger L)
```

This is the GKSL dissipator primitive. Terrain generators combine this
dissipator with sheet Hamiltonian commutators.

## Four Terrain Families And Eight Terrain Laws

There are four terrain families:

```text
Se, Ne, Ni, Si
```

Each has a left/type-1 and right/type-2 realization. That gives eight terrain
generator laws.

### Se: Funnel / Cannon

Left / Type 1 / Funnel:

```text
X_Se,L(rho)
= lambda_Se,L sum_{j=x,y,z} D[sigma_j](rho)
  - i epsilon_Se,L [H_L, rho]
```

or in the more general `terrains.md` form:

```text
X_F^L(rho_L)
= sum_k D[L_k^{F,L}](rho_L)
  - i epsilon_F,L [H_L, rho_L]
```

Right / Type 2 / Cannon:

```text
X_Se,R(rho)
= lambda_Se,R sum_{j=x,y,z} D[sigma_j](rho)
  - i epsilon_Se,R [H_R, rho]
```

or:

```text
X_C^R(rho_R)
= sum_k D[L_k^{C,R}](rho_R)
  - i epsilon_C,R [H_R, rho_R]
```

Structural read:

```text
Se is expansion / open-isothermal / dissipative release.
Funnel and Cannon are the left/right sheet realizations.
```

### Ne: Vortex / Spiral

Left / Type 1 / Vortex:

```text
X_Ne,L(rho) = -i[H_L, rho]
```

or with weak dissipator:

```text
X_V^L(rho_L)
= -i[H_L, rho_L]
  + epsilon_V,L sum_k D[M_k^{V,L}](rho_L)
```

Right / Type 2 / Spiral:

```text
X_Ne,R(rho) = -i[H_R, rho]
```

or:

```text
X_S^R(rho_R)
= -i[H_R, rho_R]
  + epsilon_S,R sum_k D[M_k^{S,R}](rho_R)
```

Structural read:

```text
Ne is expansion / closed-adiabatic dominant / Hamiltonian circulation.
Vortex and Spiral are opposite sheet circulations.
```

### Ni: Pit / Source

Left / Type 1 / Pit:

```text
X_Ni,L(rho)
= gamma_Ni,L D[sigma_-](rho)
  - i epsilon_Ni,L [H_L, rho]
```

or:

```text
X_P^L(rho_L)
= gamma_P,L D[sigma_-](rho_L)
  - i epsilon_P,L [H_L, rho_L]
```

Right / Type 2 / Source:

```text
X_Ni,R(rho)
= gamma_Ni,R D[sigma_+](rho)
  - i epsilon_Ni,R [H_R, rho]
```

or:

```text
X_So^R(rho_R)
= gamma_So,R D[sigma_+](rho_R)
  - i epsilon_So,R [H_R, rho_R]
```

Structural read:

```text
Ni is compression / open-isothermal / ladder-attractor dynamics.
Pit uses sigma_-.
Source uses sigma_+.
```

This is exactly where gradient-descent/ascent language must be handled with
care. The source math says ladder dissipator plus sheet Hamiltonian term, not
a generic scalar gradient stage.

### Si: Hill / Citadel

Left / Type 1 / Hill:

```text
X_Si,L(rho)
= -i[omega_L m_L . sigma, rho]
  + kappa_L (P_+^L rho P_+^L + P_-^L rho P_-^L - rho)
```

or:

```text
X_H^L(rho_L)
= -i[K_L, rho_L]
  + sum_j kappa_H,L,j (
      P_j^{H,L} rho_L P_j^{H,L}
      - 1/2(P_j^{H,L} rho_L + rho_L P_j^{H,L})
    )
```

Right / Type 2 / Citadel:

```text
X_Si,R(rho)
= -i[omega_R m_R . sigma, rho]
  + kappa_R (P_+^R rho P_+^R + P_-^R rho P_-^R - rho)
```

or:

```text
X_Ci^R(rho_R)
= -i[K_R, rho_R]
  + sum_j kappa_Ci,R,j (
      P_j^{Ci,R} rho_R P_j^{Ci,R}
      - 1/2(P_j^{Ci,R} rho_R + rho_R P_j^{Ci,R})
    )
```

Projectors:

```text
P_pm^L = 1/2(I +/- m_L . sigma)
P_pm^R = 1/2(I +/- m_R . sigma)
```

or, in the multi-projector source:

```text
P_j^{H,L}  = 1/2(I + m_j^{H,L} . sigma),  [K_L, P_j^{H,L}] = 0
P_j^{Ci,R}= 1/2(I + m_j^{Ci,R}. sigma),  [K_R, P_j^{Ci,R}] = 0
```

Structural read:

```text
Si is compression / closed-adiabatic / retained-strata projector dynamics.
Hill and Citadel are opposite sheet retained-strata realizations.
```

## Eight Terrain Laws Summary

| Family | Left / Type 1 | Right / Type 2 | Core difference |
|---|---|---|---|
| `Se` | Funnel `X_F^L` | Cannon `X_C^R` | opposite sheet plus distinct dissipator family |
| `Ne` | Vortex `X_V^L` | Spiral `X_S^R` | `H_L=+H0` vs `H_R=-H0` circulation |
| `Ni` | Pit `X_P^L` with `sigma_-` | Source `X_So^R` with `sigma_+` | sink/source ladder orientation |
| `Si` | Hill `X_H^L` | Citadel `X_Ci^R` | retained strata on opposite sheets |

## Four Loop Objects

`terrains.md` gives four loop objects:

```text
Type 1 inner loop = (rho_L, Gamma_f^L)
Type 1 outer loop = (rho_L, Gamma_b^L)
Type 2 inner loop = (rho_R, Gamma_f^R)
Type 2 outer loop = (rho_R, Gamma_b^R)
```

where:

```text
Gamma_f^L != Gamma_b^L
Gamma_f^R != Gamma_b^R
H_L != H_R
```

This source says both engine types have inner=fiber and outer=base in that
particular convention.

The AXES/JUNGIAN atlas has another chart convention where type-two outer is
associated with fiber and type-two inner with lifted base. That is a chart
grammar difference that must be kept visible, not smoothed.

## Sixteen Terrain Placements

Terrain placements are not the same object as the 16 ordered tokens.

Terrain placement object:

```text
(terrain generator X_{tau,s}, loop path Gamma_{ell}^s)
```

where:

```text
tau in {Se,Ne,Ni,Si}
s in {L,R}
ell in {inner,outer}
```

Full terrain placements:

| # | Placement | Exact object |
|---|---|---|
| 1 | `Se / Funnel / Type 1 inner` | `(X_F^L, Gamma_f^L)` |
| 2 | `Ne / Vortex / Type 1 inner` | `(X_V^L, Gamma_f^L)` |
| 3 | `Ni / Pit / Type 1 inner` | `(X_P^L, Gamma_f^L)` |
| 4 | `Si / Hill / Type 1 inner` | `(X_H^L, Gamma_f^L)` |
| 5 | `Se / Funnel / Type 1 outer` | `(X_F^L, Gamma_b^L)` |
| 6 | `Ne / Vortex / Type 1 outer` | `(X_V^L, Gamma_b^L)` |
| 7 | `Ni / Pit / Type 1 outer` | `(X_P^L, Gamma_b^L)` |
| 8 | `Si / Hill / Type 1 outer` | `(X_H^L, Gamma_b^L)` |
| 9 | `Se / Cannon / Type 2 inner` | `(X_C^R, Gamma_f^R)` |
| 10 | `Ne / Spiral / Type 2 inner` | `(X_S^R, Gamma_f^R)` |
| 11 | `Ni / Source / Type 2 inner` | `(X_So^R, Gamma_f^R)` |
| 12 | `Si / Citadel / Type 2 inner` | `(X_Ci^R, Gamma_f^R)` |
| 13 | `Se / Cannon / Type 2 outer` | `(X_C^R, Gamma_b^R)` |
| 14 | `Ne / Spiral / Type 2 outer` | `(X_S^R, Gamma_b^R)` |
| 15 | `Ni / Source / Type 2 outer` | `(X_So^R, Gamma_b^R)` |
| 16 | `Si / Citadel / Type 2 outer` | `(X_Ci^R, Gamma_b^R)` |

This is the terrain math layer that was missing.

## Relationship To Operator Tokens

The ordered tokens:

```text
TiSe, SeTi, FiSe, SeFi, ...
```

are not the same as:

```text
Se / Funnel / Type 1 inner
```

They are a judging/operator grammar over perceiving topology labels.

Terrain placement includes:

```text
sheet
loop carrier
terrain generator law
spinor vector field
density law
```

Token includes:

```text
topology label
operator family
operator/terrain precedence
```

The correct source-safe relation is:

```text
operator tokens dress or select operations on terrain placements,
but they do not replace terrain generator laws.
```

Any sim or doc that says:

```text
16 placements = 16 ordered tokens
```

without qualification is wrong.

## Corrected Count Table

| Layer | Count | Object |
|---|---:|---|
| terrain families | 4 | `Se`, `Ne`, `Ni`, `Si` |
| sheet terrain laws | 8 | `Funnel`, `Cannon`, `Vortex`, `Spiral`, `Pit`, `Source`, `Hill`, `Citadel` |
| loop objects | 4 | `(rho_L,Gamma_f^L)`, `(rho_L,Gamma_b^L)`, `(rho_R,Gamma_f^R)`, `(rho_R,Gamma_b^R)` |
| terrain placements | 16 | 8 terrain laws placed on inner/outer sheet loops |
| judging operators | 4 | `Ti`, `Te`, `Fi`, `Fe` |
| signed judging variants | 8 | 4 operators x up/down precedence |
| ordered tokens | 16 | 4 topology labels x 2 operator families x 2 precedence signs |

## Corrected Stack

```text
F01 + N01
  -> C
  -> M(C)
  -> S3 spinor / D(C2) density carrier
  -> Hopf torus loop geometry
  -> Weyl sheet split H_L=+H0, H_R=-H0
  -> 8 terrain generator laws X_{tau,L/R}
  -> 16 terrain placements (X_{tau,s}, Gamma_{inner/outer}^s)
  -> 4 judging operator channels Ti/Te/Fi/Fe
  -> 16 ordered tokens as operator/topology/precedence grammar
  -> engine charts that compose/dress terrain placements with operator tokens
  -> open flux candidates from stagewise deltas
  -> open Xi/Phi0 cut-state bridge
```

## What This Corrects

| Previous collapse | Correction |
|---|---|
| terrains as just `Se/Ne/Ni/Si` labels | each terrain has left/right generator laws with distinct dissipator/Hamiltonian content |
| 16 placements as 16 tokens | there are 16 terrain placements and 16 ordered tokens, different layers |
| engine type as only operator pair | engine type also has sheet, loop, terrain-generator, and Hamiltonian-sign content |
| flux as pre-axial root | flux remains candidate readout from terrain-stage deltas |
| Te/Ni/Si as generic gradient labels | terrain laws specify ladder dissipators, projector dephasing, and sheet Hamiltonian terms |

## Minimum Runtime Fields For Future Sims

Every terrain-stage sim should record:

```text
terrain_family: Se | Ne | Ni | Si
terrain_realization: Funnel | Cannon | Vortex | Spiral | Pit | Source | Hill | Citadel
sheet: L | R
H_sheet: +H0 | -H0
terrain_generator: explicit X_* formula / parameter set
loop_path: Gamma_f | Gamma_b
spinor_field: Y_in | Y_out
density_visibility: stationary | traversing
operator_token: optional TiSe / SeTi / ...
judging_operator: optional Ti | Te | Fi | Fe
operator_precedence: optional operator_first | terrain_first
axis6_action_side: optional left_action | right_action | both
closure_type: gksl | unitary_adjoint | kraus | commutator | mixed
readouts: trace, positivity, entropy, Bloch delta, sheet delta, flux candidate
```

Without those fields, a result cannot honestly claim to have run the terrain
math.

## Bottom Line

The terrain math is not:

```text
four labels
```

and it is not:

```text
the 16 ordered operator tokens
```

The terrain math is:

```text
8 sheet-specific GKSL/Hamiltonian generator laws
placed on 4 sheet-loop carriers,
giving 16 terrain placements before judging-operator token dressing.
```

That is the layer the previous layout failed to carry.
