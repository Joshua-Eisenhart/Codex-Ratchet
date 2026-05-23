# QIT Engine Full Explicit Math Packet

**Created:** 2026-05-22
**Status:** source-grounded synthesis plus fenced exploratory bridges; no runtime promotion

## Purpose

This packet restores the math that kept getting compressed away in chat:

```text
1. geometric constraint manifold
2. Hopf / Weyl carrier geometry
3. four terrain families and eight terrain generator laws
4. sixteen terrain placements
5. four intrinsic judging operators
6. Axis 5 dephasing/rotation algebra and the gradient/spectral reading
7. Axis 6 left/right action and physical closure
8. ordered-token grammar versus terrain-placement grammar
9. open flux / Axis 0 bridge boundaries
```

The main correction is that the system has several nearby but distinct layers.
They cannot be collapsed.

```text
terrain family       != judging operator
terrain generator    != ordered token
terrain placement    != Jungian label
operator map         != signed role word
left/right action    != standalone physical channel
flux candidate       != admitted root constraint
```

## Source And Authority Fence

Primary source anchors used for this synthesis:

```text
READ ONLY Reference Docs/operator math explicit.md
READ ONLY Reference Docs/terrain math.md
READ ONLY Reference Docs/terrains.md
READ ONLY Reference Docs/apple axes terrain operator math.md
READ ONLY Reference Docs/JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP copy.md
READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md
READ ONLY Reference Docs/Weyl Flux.md
system_v5/docs/17_actual_lego_registry.md
```

Derived / exploratory surfaces used only as intermediate audits:

```text
system_v5/ops/TERRAIN_GENERATOR_SOURCE_LAYOUT_20260522.md
system_v5/ops/AXIS5_AXIS6_EXPLORATORY_QIT_WORKOUT_20260522.md
system_v5/ops/AXIS3_ENGINE_FLUX_PLACEMENT_EXPLORATORY_AUDIT_20260522.md
system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md
```

This packet does not override the read-only source docs. It is an explicit
working synthesis and audit target.

## Audit Delta From The Claude Layout

Claude's recovered layout is useful, but only after separating source-locked
claims from exploratory bridges.

Accepted improvements:

```text
1. add the explicit A1/A6 derived-chain rules:
   A1 is derived from A0 and A2
   b6 = - b0 b3

2. add the engine-type triple-swap:
   fiber/base
   deductive/inductive
   outer/inner chart role

3. state that fiber/base is the geometry-level A3 anchor,
   while outer/inner is chart-relative by engine type

4. preserve FGA/FSA as exploratory names only,
   with the admission tests tied to the source operator families

5. keep flux as an open derived candidate family,
   not a pre-axial root
```

Rejected or fenced parts:

```text
1. "flux as pre-axial" is not admitted by source.
   It remains a serious candidate placement, not a root.

2. "A6 = left/right action" is the QIT realization/audit layer,
   while the active source token law is still up/down precedence
   with b6 = -b0 b3. Both must be kept visible.

3. "A4 = TeFi vs FeTi pair" is only safe as the implemented
   runtime correlation of the deeper loop-order family, not as a
   replacement for the UEUE/EUEU order object.

4. "FGA/FSA" are not names to lock yet. They are useful only if
   they reduce to {Ti,Te} dephasing/pinching and {Fi,Fe}
   Hamiltonian rotations.
```

## The Two Different Sixteens

There are two separate 16-count objects.

### 16 Ordered Tokens

These are grammar tokens:

```text
terrain/topology family x judging operator family x precedence
```

Example:

```text
TiSe, SeTi, FiSe, SeFi, ...
```

They are labels for ordered function-token rows.

### 16 Terrain Placements

These are generator/path placements:

```text
4 terrain families x 2 Weyl sheets x 2 loop paths
```

Equivalently:

```text
(terrain generator X_{tau,s}, loop vector field Y_l)

tau in {Se, Ne, Ni, Si}
s   in {L, R}
l   in {in, out}
```

These are actual dynamical placement objects.

The two lists are related, but they are not identical. Any future sim must say
which one it is testing.

## Fixed Notation

Hilbert space:

```text
H = C^2
B(H) = 2 x 2 complex matrices
D(H) = {rho in B(H) : rho = rho^dagger, rho >= 0, Tr(rho)=1}
```

Pauli basis:

```text
I       = [[1, 0], [0, 1]]
sigma_x = [[0, 1], [1, 0]]
sigma_y = [[0,-i], [i, 0]]
sigma_z = [[1, 0], [0,-1]]
```

Ladder matrices, source convention:

```text
sigma_- = [[0, 0], [1, 0]]
sigma_+ = [[0, 1], [0, 0]]
```

Projectors:

```text
P_0 = (I + sigma_z)/2 = [[1,0],[0,0]]
P_1 = (I - sigma_z)/2 = [[0,0],[0,1]]

Q_+ = (I + sigma_x)/2 = (1/2)[[1,1],[1,1]]
Q_- = (I - sigma_x)/2 = (1/2)[[1,-1],[-1,1]]
```

Generic density matrix:

```text
rho = [[a, u - i v],
       [u + i v, d]]

a,d,u,v real
a + d = 1
rho >= 0
```

Bloch coordinates:

```text
rho = (1/2)(I + x sigma_x + y sigma_y + z sigma_z)

x = 2u
y = 2v
z = a - d
a = (1+z)/2
d = (1-z)/2
```

Purity and entropy:

```text
Tr(rho^2) = (1 + ||r||^2)/2
lambda_+/- = (1 +/- ||r||)/2
S(rho) = -lambda_+ log(lambda_+) - lambda_- log(lambda_-)
```

## Root Constraint Layer

The root admissibility conditions are not optional engine settings.

```text
F01_FINITUDE:
  dim(H) < infinity
  finite probe family
  finite operator registry
  finite path encodings

N01_NONCOMMUTATION:
  AB != BA in general
  A rho != rho A in general
```

Consequences:

```text
1. all spectra are finite
2. all probes are finite witnesses
3. left/right action is observable when [A,rho] != 0
4. operator order cannot be erased by default
5. no primitive infinite bath, continuum field, or unbounded closure is admitted
```

## Constraint Manifold Stack

The manifold is not downstream decoration. It is the admissible surface on
which operators, terrains, loops, and engines run.

```text
root constraints
  -> admissibility set C
  -> M(C) = {x : x is admissible under C}
  -> geometry on M(C)
  -> axes A_i : M(C) -> V_i
  -> engine placements and trajectories
```

Concrete current carrier stack:

| Layer | Object | Formula |
|---|---|---|
| finite state | density matrices | `D(C^2)` |
| spinor carrier | normalized spinor | `S^3 = {psi in C^2 : ||psi||=1}` |
| Hopf projection | spinor to Bloch | `pi(psi)=psi^dagger sigma psi in S^2` |
| density reduction | spinor to state | `rho(psi)=psi psi^dagger` |
| torus family | Hopf tori | `T_eta subset S^3` |
| loop paths | fiber and lifted base | `gamma_in`, `gamma_out` |
| Weyl sheets | left/right signed Hamiltonians | `H_L=+H0`, `H_R=-H0` |
| engine runtime | staged maps on sheets and loops | `rho -> Phi_stage(rho)` |
| bridge target | geometry/history to cut-state | `Xi : geometry/history -> rho_AB` |
| Axis 0 kernel | signed cut functional | `Phi_0(rho_AB)` |

## Hopf / Torus / Weyl Geometry

Spinor chart:

```text
psi_s(phi, chi; eta)
= [ exp(i(phi + chi)) cos eta,
    exp(i(phi - chi)) sin eta ]^T

s in {L,R}
phi, chi in [0, 2pi)
eta in [0, pi/2]
```

Density:

```text
rho_s(phi,chi;eta)
= [[cos^2 eta,                     exp(2i chi) cos eta sin eta],
   [exp(-2i chi) cos eta sin eta,  sin^2 eta]]
```

Bloch vector:

```text
r_s(phi,chi;eta)
= (sin(2eta) cos(2chi),
   -sin(2eta) sin(2chi),
   cos(2eta))
```

The negative `r_y` sign follows from the stated spinor chart and the standard
Pauli `sigma_y` convention. The working-math audit checks the fixture
`(phi, chi, eta) = (0, pi/4, pi/4)`, where the density has
`tr(rho sigma_y) = -1`; the plus-sign transcription fails that fixture.

Hopf connection:

```text
A = -i psi_s^dagger d psi_s
  = d phi + cos(2 eta) d chi
```

Fiber loop:

```text
gamma_in^s(u) = psi_s(phi_0 + u, chi_0; eta_0)
rho_in^s(u)  = rho_s(phi_0, chi_0; eta_0)
```

The fiber loop changes spinor phase but is density-stationary.

Lifted-base loop:

```text
gamma_out^s(u)
= psi_s(phi_0 - cos(2 eta_0)u, chi_0 + u; eta_0)

A(dot gamma_out^s)=0
```

Density along lifted base:

```text
rho_out^s(u)
= [[cos^2 eta_0,                         exp(2i(chi_0+u)) cos eta_0 sin eta_0],
   [exp(-2i(chi_0+u)) cos eta_0 sin eta_0, sin^2 eta_0]]
```

The lifted-base loop is density-visible.

Loop vector fields:

```text
Y_in psi_s = partial_phi psi_s
= i [ exp(i(phi+chi)) cos eta,
      exp(i(phi-chi)) sin eta ]^T
```

```text
Y_out psi_s = (-cos(2eta) partial_phi + partial_chi) psi_s
= i [ (1 - cos 2eta) exp(i(phi+chi)) cos eta,
     -(1 + cos 2eta) exp(i(phi-chi)) sin eta ]^T
```

Weyl Hamiltonians:

```text
H_0 = n_x sigma_x + n_y sigma_y + n_z sigma_z

H_L = +H_0
H_R = -H_0
```

Sheet flows:

```text
dot rho_L = -i[H_L, rho_L]
dot r_L   =  2 n x r_L

dot rho_R = -i[H_R, rho_R]
dot r_R   = -2 n x r_R
```

The left/right Weyl sign is a real Hamiltonian sign flip, not a narrative
label.

## GKSL Dissipator Primitive

Use:

```text
D[L](rho)
= L rho L^dagger - (1/2)(L^dagger L rho + rho L^dagger L)
```

If `L = sigma_j`, then `L^dagger L = I`, so:

```text
D[sigma_j](rho)=sigma_j rho sigma_j - rho
```

Bloch effects:

```text
D[sigma_x]:
  dot x = 0
  dot y = -2y
  dot z = -2z

D[sigma_y]:
  dot x = -2x
  dot y = 0
  dot z = -2z

D[sigma_z]:
  dot x = -2x
  dot y = -2y
  dot z = 0
```

Therefore:

```text
sum_{j=x,y,z} D[sigma_j]:
  dot r = -4 r
```

with rate multiplier `lambda`, `dot r = -4 lambda r`.

## Terrain Families

The four terrain families are not judging operators.

```text
Se = expansion, open/isothermal, direct frame
Ne = expansion, closed/adiabatic-dominant, direct frame
Ni = compression, open/isothermal, conjugated frame
Si = compression, closed/adiabatic, conjugated frame
```

They are topology-and-flow classes on the carrier geometry.

The eight terrain laws arise by placing the four families on the two Weyl
sheets:

```text
Se: Funnel  / Cannon
Ne: Vortex  / Spiral
Ni: Pit     / Source
Si: Hill    / Citadel
```

## Eight Terrain Generator Laws

### Se / Funnel And Cannon

Minimal Pauli-isotropic form:

```text
X_Se,L(rho)
= lambda_Se,L sum_{j=x,y,z} D[sigma_j](rho)
  - i epsilon_Se,L [H_L, rho]

X_Se,R(rho)
= lambda_Se,R sum_{j=x,y,z} D[sigma_j](rho)
  - i epsilon_Se,R [H_R, rho]
```

General source form:

```text
X_F^L(rho_L)
= sum_k D[L_k^{F,L}](rho_L)
  - i epsilon_F,L [H_L, rho_L]

X_C^R(rho_R)
= sum_k D[L_k^{C,R}](rho_R)
  - i epsilon_C,R [H_R, rho_R]
```

If the Pauli-isotropic form is used, Bloch dynamics are:

```text
Type 1 / left:
  dot r = -4 lambda_Se,L r + 2 epsilon_Se,L n x r

Type 2 / right:
  dot r = -4 lambda_Se,R r - 2 epsilon_Se,R n x r
```

Interpretation:

```text
Se is dissipative release / open expansion.
Funnel and Cannon differ by sheet sign and possible distinct dissipator family.
```

### Ne / Vortex And Spiral

Minimal source form:

```text
X_Ne,L(rho) = -i[H_L, rho]
X_Ne,R(rho) = -i[H_R, rho]
```

Weak-dissipator source form:

```text
X_V^L(rho_L)
= -i[H_L, rho_L]
  + epsilon_V,L sum_k D[M_k^{V,L}](rho_L)

X_S^R(rho_R)
= -i[H_R, rho_R]
  + epsilon_S,R sum_k D[M_k^{S,R}](rho_R)
```

Pure Hamiltonian Bloch laws:

```text
Type 1 / left:
  dot r =  2 n x r

Type 2 / right:
  dot r = -2 n x r
```

Interpretation:

```text
Ne is circulation / adiabatic-dominant expansion.
Vortex and Spiral are opposite sheet circulations.
```

### Ni / Pit And Source

Source matrices:

```text
sigma_- = [[0,0],[1,0]]
sigma_+ = [[0,1],[0,0]]
```

Generator laws:

```text
X_Ni,L(rho)
= gamma_Ni,L D[sigma_-](rho)
  - i epsilon_Ni,L [H_L, rho]

X_Ni,R(rho)
= gamma_Ni,R D[sigma_+](rho)
  - i epsilon_Ni,R [H_R, rho]
```

General source notation:

```text
X_P^L(rho_L)
= gamma_P,L D[sigma_-](rho_L)
  - i epsilon_P,L [H_L, rho_L]

X_So^R(rho_R)
= gamma_So,R D[sigma_+](rho_R)
  - i epsilon_So,R [H_R, rho_R]
```

Ladder dissipator Bloch effects with the source matrix convention:

```text
D[sigma_-]:
  dot x = -x/2
  dot y = -y/2
  dot z = -(1+z)
  fixed point z = -1

D[sigma_+]:
  dot x = -x/2
  dot y = -y/2
  dot z = 1-z
  fixed point z = +1
```

With rates and sheet Hamiltonians:

```text
Pit:
  dot x = -(gamma_P,L/2)x + 2 epsilon_P,L (n x r)_x
  dot y = -(gamma_P,L/2)y + 2 epsilon_P,L (n x r)_y
  dot z = -gamma_P,L(1+z) + 2 epsilon_P,L (n x r)_z

Source:
  dot x = -(gamma_So,R/2)x - 2 epsilon_So,R (n x r)_x
  dot y = -(gamma_So,R/2)y - 2 epsilon_So,R (n x r)_y
  dot z =  gamma_So,R(1-z) - 2 epsilon_So,R (n x r)_z
```

Interpretation:

```text
Ni is ladder-attractor compression.
Pit uses sigma_- and pulls toward z=-1 under the source convention.
Source uses sigma_+ and pulls toward z=+1 under the source convention.
```

If a sim swaps the ladder convention, the signs must be recorded in the
receipt.

### Si / Hill And Citadel

Projectors:

```text
P_pm^L = (1/2)(I +/- m_L . sigma)
P_pm^R = (1/2)(I +/- m_R . sigma)
```

Minimal source form:

```text
X_Si,L(rho)
= -i[omega_L m_L . sigma, rho]
  + kappa_L(P_+^L rho P_+^L + P_-^L rho P_-^L - rho)

X_Si,R(rho)
= -i[omega_R m_R . sigma, rho]
  + kappa_R(P_+^R rho P_+^R + P_-^R rho P_-^R - rho)
```

General retained-strata source form:

```text
X_H^L(rho_L)
= -i[K_L, rho_L]
  + sum_j kappa_H,L,j(
      P_j^{H,L} rho_L P_j^{H,L}
      - (1/2)(P_j^{H,L} rho_L + rho_L P_j^{H,L})
    )

[K_L, P_j^{H,L}] = 0
```

```text
X_Ci^R(rho_R)
= -i[K_R, rho_R]
  + sum_j kappa_Ci,R,j(
      P_j^{Ci,R} rho_R P_j^{Ci,R}
      - (1/2)(P_j^{Ci,R} rho_R + rho_R P_j^{Ci,R})
    )

[K_R, P_j^{Ci,R}] = 0
```

For one projector axis `m` and Hamiltonian `H=omega m.sigma`, Bloch dynamics:

```text
dot r = 2 omega m x r - kappa( r - (m.r)m )
```

The transverse component to `m` decays; the component along `m` is retained.

Interpretation:

```text
Si is retained-strata projector dynamics.
Hill and Citadel are opposite sheet retained-strata realizations.
```

This is not the same as the Ni ladder sink/source. Si compresses coherence
onto invariant strata; Ni uses ladder dissipators with pole attractors.

## Sixteen Terrain Placements

Terrain placement object:

```text
(X_{tau,s}, Y_l)

tau in {Se,Ne,Ni,Si}
s   in {L,R}
l   in {in,out}
```

Equivalently:

```text
(dot psi_s, dot rho_s)
= (Omega_{tau,s,l} Y_l psi_s, X_{tau,s}(rho_s))
```

Full list:

| # | Placement | Generator/path object |
|---|---|---|
| 1 | Se/Funnel/inner | `(X_Se,L, Y_in)` |
| 2 | Se/Funnel/outer | `(X_Se,L, Y_out)` |
| 3 | Ne/Vortex/inner | `(X_Ne,L, Y_in)` |
| 4 | Ne/Vortex/outer | `(X_Ne,L, Y_out)` |
| 5 | Ni/Pit/inner | `(X_Ni,L, Y_in)` |
| 6 | Ni/Pit/outer | `(X_Ni,L, Y_out)` |
| 7 | Si/Hill/inner | `(X_Si,L, Y_in)` |
| 8 | Si/Hill/outer | `(X_Si,L, Y_out)` |
| 9 | Se/Cannon/inner | `(X_Se,R, Y_in)` |
| 10 | Se/Cannon/outer | `(X_Se,R, Y_out)` |
| 11 | Ne/Spiral/inner | `(X_Ne,R, Y_in)` |
| 12 | Ne/Spiral/outer | `(X_Ne,R, Y_out)` |
| 13 | Ni/Source/inner | `(X_Ni,R, Y_in)` |
| 14 | Ni/Source/outer | `(X_Ni,R, Y_out)` |
| 15 | Si/Citadel/inner | `(X_Si,R, Y_in)` |
| 16 | Si/Citadel/outer | `(X_Si,R, Y_out)` |

This is the terrain math that must not be lost.

## Four Intrinsic Judging Operators

The four intrinsic operator maps are:

```text
Ti, Te, Fi, Fe
```

`UP` and `DOWN` are not additional intrinsic operator maps. They are
precedence/action-side placements that only become meaningful after a terrain
or composition context is named.

### Ti: z-Basis Pinching

Channel:

```text
Ti_q(rho)
= (1-q1)rho + q1(P_0 rho P_0 + P_1 rho P_1)
```

Matrix action:

```text
[[a, b], [c, d]]
  -> [[a, (1-q1)b], [(1-q1)c, d]]
```

Bloch action:

```text
(x,y,z) -> ((1-q1)x, (1-q1)y, z)
```

Continuous generator:

```text
L_Ti(rho) = (kappa1/2)(sigma_z rho sigma_z - rho)

dot x = -kappa1 x
dot y = -kappa1 y
dot z = 0
```

Pauli transfer matrix:

```text
PTM(Ti_q) = diag(1, 1-q1, 1-q1, 1)
GEN(Ti)   = diag(0, -kappa1, -kappa1, 0)
```

Fixed algebra:

```text
Fix(Ti) = span{I, sigma_z}
```

Distance-to-fixed-algebra functional:

```text
D_z(rho) = ||rho - E_z(rho)||_2^2 = (x^2 + y^2)/2
D_z(Ti_t(rho)) = exp(-2 kappa1 t) D_z(rho)
```

### Te: x-Basis Pinching

Channel:

```text
Te_q(rho)
= (1-q2)rho + q2(Q_+ rho Q_+ + Q_- rho Q_-)
```

Bloch action:

```text
(x,y,z) -> (x, (1-q2)y, (1-q2)z)
```

Continuous generator:

```text
L_Te(rho) = (kappa2/2)(sigma_x rho sigma_x - rho)

dot x = 0
dot y = -kappa2 y
dot z = -kappa2 z
```

Pauli transfer matrix:

```text
PTM(Te_q) = diag(1, 1, 1-q2, 1-q2)
GEN(Te)   = diag(0, 0, -kappa2, -kappa2)
```

Fixed algebra:

```text
Fix(Te) = span{I, sigma_x}
```

Distance-to-fixed-algebra functional:

```text
D_x(rho) = ||rho - E_x(rho)||_2^2 = (y^2 + z^2)/2
D_x(Te_t(rho)) = exp(-2 kappa2 t) D_x(rho)
```

This is the precise version of "Te descent": Te descends `D_x`. It may
increase von Neumann entropy, decrease purity, and decrease target-distance at
the same time. The functional must be named.

### Fi: x-Axis Hamiltonian Rotation

Channel:

```text
Fi_theta(rho) = U_x(theta) rho U_x(theta)^dagger
U_x(theta) = exp(-i theta sigma_x/2)
```

Bloch action:

```text
x' = x
y' = y cos(theta) - z sin(theta)
z' = y sin(theta) + z cos(theta)
```

Generator:

```text
L_Fi(rho) = -i[(omega3/2)sigma_x, rho]

dot x = 0
dot y = -omega3 z
dot z =  omega3 y
```

Pauli transfer matrix:

```text
PTM(Fi_theta) =
[[1, 0, 0,          0],
 [0, 1, 0,          0],
 [0, 0, cos theta, -sin theta],
 [0, 0, sin theta,  cos theta]]
```

Invariants:

```text
spec(rho) preserved
S(rho) preserved
Tr(rho^2) preserved
||r|| preserved
```

### Fe: z-Axis Hamiltonian Rotation

Channel:

```text
Fe_phi(rho) = U_z(phi) rho U_z(phi)^dagger
U_z(phi) = exp(-i phi sigma_z/2)
```

Bloch action:

```text
x' = x cos(phi) - y sin(phi)
y' = x sin(phi) + y cos(phi)
z' = z
```

Generator:

```text
L_Fe(rho) = -i[(omega4/2)sigma_z, rho]

dot x = -omega4 y
dot y =  omega4 x
dot z = 0
```

Pauli transfer matrix:

```text
PTM(Fe_phi) =
[[1, 0,        0,       0],
 [0, cos phi, -sin phi, 0],
 [0, sin phi,  cos phi, 0],
 [0, 0,        0,       1]]
```

Invariants:

```text
spec(rho) preserved
S(rho) preserved
Tr(rho^2) preserved
||r|| preserved
```

## Axis 5: Dephasing/Rotation Algebra And Gradient/Spectral Reading

Source anchor:

```text
Axis 5 = {Ti, Te} versus {Fi, Fe}
```

The clean QIT reading:

| Side | Operators | Channel class | Generator class | Geometry |
|---|---|---|---|---|
| dephasing/projection | `Ti`, `Te` | pinching / conditional expectation semigroups | self-adjoint negative contractions on transverse subspaces | contraction to a commutative fixed algebra |
| rotation/unitary | `Fi`, `Fe` | inner automorphisms | skew-adjoint Hamiltonian derivations | constant-spectrum orbit motion |

This is the source-grounded form.

The richer exploratory language:

```text
finite-gradient algebra
finite-spectral algebra
```

is only safe if reduced to the exact operator families:

```text
finite-gradient algebra -> finite dephasing/pinching contractions in {Ti, Te}
finite-spectral algebra -> finite Hamiltonian adjoint rotations in {Fi, Fe}
```

Do not let "gradient" mean every Lindbladian or every optimization process.
Do not let "spectral" mean every projector/filter.

### Finite Dephasing / Pinching Algebra

For an involution `P = P^dagger`, `P^2=I`, define:

```text
L_P(rho) = (kappa/2)(P rho P - rho)
Phi_t = exp(t L_P)
```

For `P=sigma_z`, this is `Ti`.

For `P=sigma_x`, this is `Te`.

Limit:

```text
lim_{t -> infinity} Phi_t(rho)
= E_P(rho)
```

where `E_P` is the conditional expectation onto the algebra commuting with
`P`.

Fixed algebras:

```text
E_z(rho) = P_0 rho P_0 + P_1 rho P_1
Fix(Ti) = {rho : [rho, sigma_z]=0}

E_x(rho) = Q_+ rho Q_+ + Q_- rho Q_-
Fix(Te) = {rho : [rho, sigma_x]=0}
```

Lyapunov-style distances:

```text
D_z = (x^2 + y^2)/2
D_x = (y^2 + z^2)/2
```

Dynamics:

```text
dD_z/dt under Ti = -2 kappa1 D_z
dD_x/dt under Te = -2 kappa2 D_x
```

Entropy caveat:

```text
unital qubit dephasing is entropy non-decreasing
general Lindblad dynamics can increase or decrease entropy
```

So any "gradient descent" claim must state the functional:

```text
descent of D_x
descent of D_z
descent of purity
ascent of von Neumann entropy
descent of free energy
```

These are different claims.

### Finite Spectral / Hamiltonian Algebra

For a Hamiltonian `H=H^dagger`:

```text
L_H(rho) = -i[H,rho]
Phi_t(rho) = exp(-iHt) rho exp(iHt)
```

For `H=(omega3/2)sigma_x`, this is `Fi`.

For `H=(omega4/2)sigma_z`, this is `Fe`.

Properties:

```text
Phi_t is CPTP
Phi_t is reversible
Phi_t preserves spectrum
Phi_t preserves entropy
Phi_t preserves purity
Phi_t has no attractor by itself
```

Spectral decomposition:

```text
H = sum_n lambda_n |n><n|

rho(t) = sum_{m,n} exp(-i(lambda_m-lambda_n)t)
         rho_{mn} |m><n|
```

The off-diagonal entries rotate by Bohr frequencies; eigenvalues of `rho` do
not change.

So "broadcast", "filtering", "entrainment", or "damping" are not intrinsic to
`Fi` or `Fe` alone. They require a terrain, reference, dissipative coupling, or
readout.

## Axis 6: Left/Right Action

Source/formal anchor:

```text
Axis 6 = left action versus right action
```

Primitive maps:

```text
L_A(rho) = A rho
R_A(rho) = rho A
```

This is meaningful because:

```text
[A,rho] = A rho - rho A != 0
```

For:

```text
A = a . sigma
rho = (1/2)(I + r . sigma)
```

commutator:

```text
[A,rho] = i (a x r) . sigma
```

Left/right action gap:

```text
gap_A(rho) = ||A rho - rho A||_F
           = sqrt(2) ||a x r||
```

Specific cases:

```text
gap_sigma_x(rho) = sqrt(2) sqrt(y^2 + z^2)
gap_sigma_z(rho) = sqrt(2) sqrt(x^2 + y^2)
```

These are not accidental. They match the transverse coordinates that `Te` and
`Ti` collapse:

```text
Te collapses y,z <-> gap_sigma_x
Ti collapses x,y <-> gap_sigma_z
```

## Axis 6 Liouville Representation

Use column vectorization:

```text
vec([[a,b],[c,d]]) = [a,c,b,d]^T
```

Identity:

```text
vec(A rho B) = (B^T otimes A) vec(rho)
```

Therefore:

```text
vec(A rho) = (I otimes A) vec(rho)
vec(rho A) = (A^T otimes I) vec(rho)
```

So:

```text
L_A ~ I otimes A
R_A ~ A^T otimes I
```

For `sigma_x`:

```text
L_X = I otimes X =
[[0,1,0,0],
 [1,0,0,0],
 [0,0,0,1],
 [0,0,1,0]]

R_X = X^T otimes I =
[[0,0,1,0],
 [0,0,0,1],
 [1,0,0,0],
 [0,1,0,0]]
```

For `sigma_z`:

```text
L_Z = I otimes Z = diag(1,-1, 1,-1)
R_Z = Z^T otimes I = diag(1, 1,-1,-1)
```

Hamiltonian closure:

```text
ad_H = L_H - R_H
-i[H,rho] = -i(L_H - R_H)vec(rho)
```

Dephasing closures:

```text
D_X = X^* otimes X - I_4
D_Z = Z^* otimes Z - I_4

L_Te = (kappa2/2)D_X
L_Ti = (kappa1/2)D_Z
```

## Axis 6 Physical Closure

Primitive one-sided actions:

```text
rho -> A rho
rho -> rho A
```

are not generally physical density channels.

For general `A`, `A rho` may fail:

```text
Hermiticity
positivity
trace-one normalization
complete positivity as a channel
```

Physical closures include:

| Closure | Formula | Status |
|---|---|---|
| commutator | `-i(A rho - rho A)` | Hamiltonian generator if `A=A^dagger` |
| anticommutator piece | `-(1/2)(M rho + rho M)` | not trace preserving alone |
| Kraus sandwich | `sum_j K_j rho K_j^dagger` | CPTP if `sum K_j^dagger K_j = I` |
| GKSL | `sum_j D[L_j](rho)` plus Hamiltonian | Markovian CPTP semigroup |
| unitary adjoint | `U rho U^dagger` | reversible CPTP channel |

Runtime implication:

```text
axis6_primitive_side = left | right | both
closure_type = commutator | anticommutator | kraus | gksl | unitary_adjoint | other
physical_checks = trace | hermiticity | positivity | complete_positivity
```

A sim that claims left/right action must expose both the primitive sidedness
and the physical closure.

## Signed Operator Variants

The source rule:

```text
UP/DOWN is not extra operator math by itself.
The operator map does not change between up and down.
```

Therefore:

```text
Ti up/down use the same Ti map
Te up/down use the same Te map
Fi up/down use the same Fi map
Fe up/down use the same Fe map
```

The signed variant can matter only through:

```text
1. token precedence: operator first versus terrain first
2. left/right primitive action inside the closed generator
3. composition with a named terrain map
4. a named functional/readout
```

Minimal falsifier:

```text
If C_up(rho) == C_down(rho) for all rho and all readouts,
then that signed variant has no runtime content for that row.
```

Functional role words require functionals:

| Role word | Minimum needed |
|---|---|
| projector | fixed algebra and idempotent projection test |
| quantizer | finite probe/support reduction test |
| gradient ascent | named functional with positive delta |
| gradient descent | same functional with negative delta |
| entrainment | phase-locking readout relative to reference |
| damping | decay of oscillatory mode or phase variance |
| broadcast | increase/spread of named spectral support |
| filtering | contraction/retention of named spectral component |

No role is admitted from the label alone.

## Ordered Token Grammar

The four terrain/topology families and four judging operators give ordered
tokens.

Native terrain/operator families:

```text
direct frame      {Se, Ne} native with {Ti, Fi}
conjugated frame  {Ni, Si} native with {Te, Fe}
```

Ordered-token table:

| Terrain | Dephasing op first | Dephasing terrain first | Rotation op first | Rotation terrain first |
|---|---|---|---|---|
| `Se` | `TiSe` | `SeTi` | `FiSe` | `SeFi` |
| `Ne` | `TiNe` | `NeTi` | `FiNe` | `NeFi` |
| `Ni` | `TeNi` | `NiTe` | `FeNi` | `NiFe` |
| `Si` | `TeSi` | `SiTe` | `FeSi` | `SiFe` |

This is the 16 ordered-token object.

It is not the same as the 16 terrain placement object.

## Engine Type Charts

Source chart for engine type one:

```text
outer loop = deductive order on lifted-base loop
inner loop = inductive order on fiber loop
```

| Step | Terrain | Outer token | Inner token |
|---|---|---|---|
| 1 | `Se` | `TiSe` | `SeFi` |
| 2 | `Ne` | `NeTi` | `FiNe` |
| 3 | `Ni` | `NiFe` | `TeNi` |
| 4 | `Si` | `FeSi` | `SiTe` |

Source chart for engine type two:

```text
outer loop = inductive order on fiber loop
inner loop = deductive order on lifted-base loop
```

| Step | Terrain | Outer token | Inner token |
|---|---|---|---|
| 1 | `Se` | `FiSe` | `SeTi` |
| 2 | `Si` | `TeSi` | `SiFe` |
| 3 | `Ni` | `NiTe` | `FeNi` |
| 4 | `Ne` | `NeFi` | `TiNe` |

Important: engine type is a table-level arrangement over:

```text
sheet sign
loop path
inner/outer chart placement
loop-order family
operator family
token precedence
terrain order
```

It is not safely reducible to one loose word like flux, chirality, A3, or A4
without a row-by-row discriminator test.

### Engine-Type Triple Swap

Engine type two is engine type one with a structured triple swap:

```text
fiber        <-> lifted base
deductive    <-> inductive
outer role   <-> inner role
```

The terrain table makes the chart-relativity explicit:

| Path class | Engine type one role | Engine type two role |
|---|---|---|
| fiber terrain rows `*_f` | inner | outer |
| lifted-base terrain rows `*_b` | outer | inner |

Therefore:

```text
geometry-level A3 anchor = fiber versus lifted base
chart-level realization  = inner versus outer
engine type controls the mapping between them
```

This is the stable reconciliation of the two phrasings. If a future sim says
`A3 = outer/inner`, it must also record the engine type; otherwise it has lost
the path geometry.

The converse is also required: if a future sim applies the Axis 6 XOR rule, it
must use the chart-level A3 bit, not raw fiber/base. Type 2 swaps the chart role
of the paths, so raw fiber/base gives the opposite A6 sign on every Type-2 row.

## Axes 0-6 Current Safe Anchors

Deep definitions for these axes are now split out in:

```text
system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md
```

That packet defines each axis as a projection/readout over `M(C)` with domain,
codomain, equations, runtime witnesses, and falsifiers. The table below is
only a compact index.

| Axis | Safe anchor | Math object |
|---|---|---|
| Axis 0 | entropy drive / later cut-state functional | torus `S(rho_bar(eta))`; later `Phi_0(rho_AB)` |
| Axis 1 | derived terrain branch split | `{Se,Ni}` vs `{Ne,Si}` |
| Axis 2 | direct vs conjugated frame | `rho` vs `V^dagger rho V` |
| Axis 3 | fiber vs lifted-base loop class | density-stationary vs density-traversing path |
| Axis 4 | loop-order family | `U o E o U o E` vs `E o U o E o U` |
| Axis 5 | operator family | `{Ti,Te}` dephasing vs `{Fi,Fe}` rotation |
| Axis 6 | precedence/action side | ordered token up/down; left/right action audit |

## Derived Axis Relations

Some axes are not free knobs in the active lower stack.

Axis 1:

```text
A1 is a derived terrain branch split from A0 and A2.
```

Source-level branch:

```text
Axis 1 = {Se, Ni} versus {Ne, Si}
```

Symbolic / taijitu correlation:

```text
Axis 1 = {Ni, Se} versus {Ne, Si}
```

The ordering in the written pair is not the important math. The partition is.
It separates the terrain branch induced by Axis 0 polarity and Axis 2 frame.

Axis 6:

```text
b_6 = - b_0 b_3
```

Binary reading:

```text
Axis 6 is equivalent to an exclusive-or relation between Axis 0 and Axis 3.
```

Here `b_3` means the chart-role bit:

```text
outer -> b_3 = +1
inner -> b_3 = -1
```

It does not mean raw fiber/base. Raw path remains the geometry witness; chart
role is the sign input to the lower-stack XOR.

Consequences:

```text
1. A6 is not an independent free bit in the lower-stack symbolic relation.
2. A6 still has a real QIT realization as left/right action.
3. A6 token precedence must be checked against the left/right action layer
   before a runtime row can claim action-sidedness.
```

Free-bit caution:

```text
The structural token system can be indexed by fewer independent bits than
the number of visible axis labels. Do not infer runtime independence from
the existence of an axis name.
```

Axis 3 caution:

```text
fiber/base is the geometry-level split
inner/outer is chart placement and can depend on engine type
```

Axis 4 caution:

```text
FeTi / TeFi are current correlations with loop-order family,
not yet proof that A4 is merely an operator-pair selector.
```

Axis 6 caution:

```text
token precedence and left/right action must be audited together;
one does not automatically prove the other in a running sim.
```

## Axis 0 Entropy Ratchet

Layered entropy structure:

| Layer | Object | Entropy/readout |
|---|---|---|
| density state | `rho in D(C^2)` | von Neumann, Renyi, purity |
| Hopf torus | orbit-averaged `rho_bar(eta)` | geometric torus entropy |
| Weyl pair | `rho_L`, `rho_R` | per-sheet entropies |
| runtime engine | `rho_E` | reduced/cut entropies if multipartite |
| bridge/cut | `rho_AB` | `S(A|B)`, `I_c`, `I(A:B)` |

Chart torus:

```text
rho_bar(eta) = average over orbit
S(rho_bar(eta))
= -cos^2(eta)log(cos^2(eta)) - sin^2(eta)log(sin^2(eta))
```

Candidate cut functionals:

```text
S(A|B) = S(rho_AB) - S(rho_B)
I_c(A > B) = S(rho_B) - S(rho_AB)
I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)
```

Strong current simple candidate:

```text
Phi_0(rho_AB) = I_c(A > B)
```

Open bridge:

```text
Xi : geometry/history -> rho_AB
```

This bridge is not closed by single-site operator math.

## Flux Boundary

Flux has been simulated in candidate/readout form. The open question is not
whether flux-like or chiral-manifold probes exist. They do. The open question
is which flux object is canonical, where it lives in the stack, and what claim
ceiling it can carry.

Existing evidence that must not be erased:

```text
1. rough GStack / constraint-manifold sidequest receipts report:
   Weyl chirality split, flux holonomy pi, stable repeat holonomy,
   transforms staying on the candidate manifold.

2. iter_160 reports Weyl-flux doctrine as derived/open and tests that
   chirality differential is nonzero only with the L/R Weyl split.

3. engine/basin sidequest iters 176-183 report T1/T2 distinct attractors,
   schedule-level pseudo-basins, four N=2 schedule attractors, and a
   coplanar basin geometry whose macro-axis aligns against the Hamiltonian
   direction.

4. later formal plan receipts route exact-torch schedule-memory, coupled E16,
   tensor, PEPS/PEPS3D first-rung, and Phi0/bridge attempts as evidence with
   explicit non-admission boundaries.
```

So the correction is:

```text
wrong: flux was not simulated
right: flux/chiral-basin candidates were simulated, but flux was not
       canonically identified or admitted as a root/axis/final mechanism
```

Flux is not admitted here as a new root constraint.

Safe status:

```text
flux = open derived candidate family
```

Candidate families:

```text
J_geom   geometric transport flux
J_chi    chirality separation flux
J_Bloch  differential Bloch current
J_ent    entropy/asymmetry current
J_cut    cut-state information current
J_axis   axis-internal readout
J_cross  coupled multi-axis observable
```

What is safe:

```text
manifold-level flux is a serious candidate placement
```

What is not safe:

```text
F0?_FLUX is already a root
flux already replaces A3
flux already determines engine type alone
```

Required discriminator:

```text
hold token chart fixed and flip sheet sign
hold sheet sign fixed and flip token chart
flip one stage only
flip all stages
measure CPTP, fixed point, basin clusters, J_chi, J_Bloch, J_ent, J_cut
```

## Full Engine Runtime Object

A stage should declare:

```text
terrain_family          tau in {Se,Ne,Ni,Si}
terrain_realization     Funnel/Cannon/Vortex/Spiral/Pit/Source/Hill/Citadel
terrain_table_id        Se_f | Se_b | Ne_f | Ne_b | Ni_f | Ni_b | Si_f | Si_b
sheet                   L | R
loop_path               in | out
path_geometry           fiber | lifted_base
chart_loop_role         inner | outer
engine_type             type_1 | type_2
terrain_generator       X_{tau,s}
spinor_vector_field     Y_in | Y_out
judging_operator        Ti | Te | Fi | Fe
axis5_family            dephasing | rotation
axis6_token_precedence  operator_first | terrain_first
axis6_primitive_side    left | right | both
closure_type            gksl | commutator | kraus | unitary_adjoint | composition
functional_readout      named functional, if role word is used
```

Physical checks:

```text
trace preservation
Hermiticity preservation
positivity
complete positivity, when a channel is claimed
CPTP Choi check, when applicable
fixed point / spectral gap, when basin is claimed
left/right action gap, when Axis 6 is claimed load-bearing
terrain law ID and source matrices
engine triple-swap consistency, when engine type is claimed
```

## Minimal Sim Falsifiers

### Terrain Falsifier

Claim:

```text
this sim tests terrain math
```

Must expose:

```text
X_{tau,s}
Y_l
sheet sign H_L or H_R
L_k or projector matrices
integration method
trace/hermiticity/positivity checks
```

Failure:

```text
only token labels appear, no terrain generator
```

### Operator Falsifier

Claim:

```text
this sim tests Ti/Te/Fi/Fe
```

Must expose:

```text
operator map
generator
PTM or Bloch action
fixed algebra or invariant
```

Failure:

```text
operator described only as "gradient", "filter", "projector", etc.
```

### Axis 5 Falsifier

Claim:

```text
Axis 5 = gradient/spectral algebra
```

Must show:

```text
{Ti,Te} side contracts to fixed algebras
{Fi,Fe} side preserves spectrum
named functional for any gradient claim
```

Failure:

```text
generic Lindblad entropy monotonicity is asserted
```

### Axis 6 Falsifier

Claim:

```text
Axis 6 is load-bearing
```

Must show:

```text
L_A(rho)=A rho
R_A(rho)=rho A
gap_A(rho)
physical closure used
token precedence relation, if claimed
```

Failure:

```text
UP/DOWN labels appear without a left/right or precedence-sensitive map
```

### Basin Falsifier

Claim:

```text
engine has attractor basin
```

Must show:

```text
same engine map
multiple initial states
convergence metric
fixed-point residual
spectral gap or contraction evidence
state-space basin versus schedule basin clearly separated
```

Failure:

```text
single trajectory or finite-sampling correlation is called a basin
```

## Bottom Line

The restored stack is:

```text
F01/N01
  -> M(C)
  -> Hopf/Weyl density manifold
  -> terrain generators X_{tau,s}
  -> loop vector fields Y_in/Y_out
  -> four judging operators Ti/Te/Fi/Fe
  -> Axis 5 dephasing/rotation split
  -> Axis 6 left/right action plus physical closure
  -> ordered token grammar
  -> engine schedules
  -> attractor/spectrum/entropy/cut-state readouts
```

The most important correction:

```text
terrain math is generator math.
operator math is channel/generator math.
token math is grammar.
axis math is projection/readout over the manifold.
```

Do not replace any one of these with the others.
