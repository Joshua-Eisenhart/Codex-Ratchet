# Geometric Constraint Manifold: Explicit Math Atlas

Date: 2026-05-30

This file replaces the earlier bad atlas. The earlier version still used an
old coordinate adapter and a 64-row label table. Those are not the source
object. They are not allowed to carry manifold claims here.

This atlas is self-contained. It defines the candidate mathematical objects to
simulate. It does not claim that any layer is complete, stacked, or admitted.
It does not select a final G-structure. It does not open flux, Xi, Phi0,
Axis0, FEP, gravity, or final physics.

The purpose is narrower and stricter:

```text
name each candidate layer or geometry object,
state its actual mathematical object,
state what has to be simulated independently,
state which later consumers remain blocked.
```

The companion execution ledger is:

```text
system_v5/ops/formal_scouts/GEOMETRIC_CONSTRAINT_MANIFOLD_CLEAR_SIM_TARGET_LEDGER_20260530.md
```

Use this atlas for definitions. Use the ledger for concrete sim rows.

## 0. What Is Forbidden As Claim-Bearing Geometry

The following objects may be useful as diagnostics, visual adapters, or
classical controls. They are not claim-bearing manifold geometry in this
program:

```text
Cartesian xyz primitives
dense full-state closure
single-qubit coordinate adapters
row labels without maps
stage tables without local cell/channel actions
scalar entropy with no finite carrier action
density-only carrier claims
flux before terrain/transport/current exists
Axis0 as a root geometry
FEP as source math
```

The source object is a finite spinor-network constraint manifold, not that
adapter.

## 1. Root Constraints

The two root constraints are not layers inside the manifold. They are the rules
that force the candidate manifold into existence.

### 1.1 Finite Carrier / Probe / Operator / Path Constraint

```text
F01:
Every admissible object must be finite at runtime.

Finite means:
  finite carrier set
  finite probe/effect set
  finite operator/channel set
  finite path/history set
  finite controls
  finite receipt
```

Mathematically:

```text
K = finite carrier complex
P = {P_1, ..., P_m} finite probes/effects
O = {O_1, ..., O_n} finite operators/channels/generators
H = {h_1, ..., h_q} finite histories/paths
```

### 1.2 Noncommuting / Order-Sensitive Constraint

```text
N01:
At least one admissible operation family must be order-sensitive.
```

Mathematically:

```text
A o B != B o A
```

or, for path histories:

```text
K_h = K_{a_T} ... K_{a_2} K_{a_1}

K_h != K_{reverse(h)}
```

or, for finite response maps:

```text
r_P(A(B(x))) != r_P(B(A(x)))
```

The commuting or order-erased control must fail to support the same claim.

## 2. The Candidate Manifold Object

The geometric constraint manifold is the survivor object created by finite
distinguishability plus order-sensitive action.

Let:

```text
C = active finite constraint family
X = finite candidate state/configuration set
```

Then:

```text
M(C) = {x in X : x survives all constraints in C}
```

Equivalence is probe-dependent:

```text
x ~_P y  iff  p(x) = p(y) for every p in P
```

The observable finite geometry is:

```text
Q_P(C) = M(C) / ~_P
```

That is the base meaning of "geometry" here: a finite survivor quotient under
finite probes and order-sensitive operations.

## 3. Category Split

These categories must not be collapsed.

### 3.1 Manifold Constraint Layers

These are nested finite mathematical objects that can restrict the same
candidate state space more and more.

```text
finite response quotient
source-native spinor network
literal shell possibility field
Hopf/nested-torus loop geometry
Clifford/quaternion/spin/twistor local structure
left/right Weyl sheet cover
eight terrain generator laws
sixteen terrain placements
local operator/channel degree-of-freedom maps
operator-terrain local cells
ordered cycle/ratchet paths
gluing/groupoid/equivariant closure
```

### 3.2 Geometry Ingredients

These are mathematical ingredients used by the layers or tested beside them:

```text
S3 unit spinors
CP1 projective spinor base
Hopf fibration
nested Hopf tori
Clifford tori
twistor incidence
finite cell complexes
spectral triples
finite effect geometries
contextuality/sheaf geometries
process POVM / quantum comb histories
```

### 3.3 G-Structure Candidates

A G-structure is not a manifold layer. It is a candidate frame/bundle
reduction that might carry the layered ratchet.

Examples:

```text
U(1)
SU(2) / Spin(3)
SO(3)
Pin / Spin
Spin^c
symplectic structure
almost complex / Kahler structure
SU(n) / Calabi-Yau type structure
G2 structure
Spin(7) structure
hybrid Hopf-spin-twistor-Clifford reductions
```

### 3.4 Readouts

Readouts run across layers when their inputs exist. They are not standalone
geometry layers.

```text
von Neumann entropy
Renyi entropy
linear entropy / purity
mutual information
conditional entropy
coherent information
relative entropy
logarithmic negativity
entanglement spectrum
path entropy
shell possibility entropy
boundary entropy
binding/correlation readouts
```

### 3.5 Downstream Consumers

These cannot be opened by labels:

```text
flux
Xi
Phi0
Axis0
FEP / Holodeck
physics / gravity model claims
final manifold admission
```

They consume lower objects. They are not root geometry.

## 4. Source-Native Local Spinor

The local carrier is a complex two-component spinor:

```text
H_site = C^2

psi_s(phi, chi; eta)
  = [ exp(i(phi + chi)) cos(eta),
      exp(i(phi - chi)) sin(eta) ]^T

s in {L, R}
phi, chi in [0, 2pi)
eta in [0, pi/2]

||psi_s|| = 1
```

The local density readout is derived from the spinor:

```text
rho_s = psi_s psi_s^dagger
```

Density matrices are allowed as local and cut readouts. They are not the root
carrier.

The source-native object preserves:

```text
spinor phase
Hopf fiber/base structure
left/right Weyl sheet sign
terrain action
operator/channel action
site/bond/face/cell locality
entropy/cut readouts tied to finite action
```

## 5. Source-Native Spinor Network

A full layer sim cannot be a single isolated spinor. It needs a finite spinor
network.

Finite carrier complex:

```text
K = (V, E, F, C3)

V  = finite sites
E  = finite bonds
F  = finite faces
C3 = finite 3-cells
```

Local site data:

```text
for each v in V:
  psi_v in C^2
  ||psi_v|| = 1
  rho_v = psi_v psi_v^dagger
```

Bond data:

```text
for each edge e = (u,v) in E:
  B_e : H_u tensor H_v -> H_u tensor H_v
```

Face/cell data:

```text
for each face f in F:
  C_f = local compatibility constraint on boundary(f)

for each cell c in C3:
  C_c = local compatibility constraint on boundary(c)
```

A spinor-network state is not just the list of site spinors. It includes
finite bond, face, and cell constraints:

```text
Psi_K = ( {psi_v}, {B_e}, {C_f}, {C_c} )
```

Allowed numerical representations include MPS, PEPS2D, and PEPS3D style
contraction carriers when they preserve the spinor-network fields above.
Those are computational representations of the spinor network, not the
ontology.

## 6. Dynamic "Breathing" Requirement

"Dynamic" means the geometry is not a frozen table. The carrier must evolve.

At minimum, a dynamic layer has:

```text
psi_v(t)
B_e(t)
C_f(t)
C_c(t)
```

with finite update:

```text
Psi_K(t + dt) = U_dt(Psi_K(t), controls_t)
```

or generator:

```text
d Psi_K / dt = X(Psi_K)
```

A breathing shell/network sim allows local contraction, expansion, warping, and
constraint tightening/loosening:

```text
site action:       psi_v(t) -> psi_v(t + dt)
bond action:       B_e(t)   -> B_e(t + dt)
face action:       C_f(t)   -> C_f(t + dt)
cell action:       C_c(t)   -> C_c(t + dt)
shell action:      Sigma_r(t) -> Sigma_{r'}(t + dt)
compatibility:     Omega_r(t) -> Omega_r(t + dt)
```

A static invariant-only check is a geometry lego at best. It is not the full
dynamic layer sim the project is aiming at.

## 7. Primary Candidate Layer Stack

This order is the current best mathematical organization. It is not final
canon. Each layer must be simulated independently before stacking claims.

### Layer 0: Finite Response / Distinguishability Quotient

Object:

```text
X = finite candidate state/configuration set
P = {E_1, ..., E_m} finite effect/probe family

E_i >= 0
sum_i E_i = I
```

Response:

```text
r_P(x) = (p_1(x), ..., p_m(x))
```

For density readouts:

```text
p_i(rho) = Tr(E_i rho)
```

Equivalence:

```text
x ~_P y  iff  r_P(x) = r_P(y)
```

Quotient:

```text
Q_P = X / ~_P
```

Why it is geometry:

```text
identity is earned by finite distinguishability under probes
```

Independent sims:

```text
generic finite POVM response quotient
SIC/POVM response geometry
MUB response geometry
finite projective design response geometry
contextuality/sheaf response geometry
process POVM / quantum comb response geometry
```

### Layer 1: Source-Native Finite Spinor Network

Object:

```text
Psi_K = (K, {psi_v}, {B_e}, {C_f}, {C_c})
```

Admissible local action:

```text
A_v : C^2 -> C^2
A_e : H_u tensor H_v -> H_u tensor H_v
A_f : H_boundary(f) -> H_boundary(f)
A_c : H_boundary(c) -> H_boundary(c)
```

Local evolution:

```text
psi_v' = normalize(A_v psi_v)
```

Network evolution:

```text
Psi_K' = A_K(Psi_K)
```

The sim must preserve phase. If phase is erased and the claim still passes, the
claim is not source-native.

Independent sims:

```text
site spinor dynamics
bond coupling dynamics
face compatibility constraints
3-cell compatibility constraints
MPS representation of the spinor network
PEPS2D representation of the spinor network
PEPS3D representation of the spinor network
tool parity where possible
```

### Layer 2: Literal Shell Possibility Field

This is the recent correction. The shell is not an abstract boundary.

For an event or point `x`:

```text
Sigma_r(x) = finite shell at radius r around x
i = r = shell scalar / clock
Omega_r(x) = finite future-possibility set carried by Sigma_r(x)
j,k = finite indices over possible refinements on the shell
```

Future-inward compression:

```text
F_in,r : Omega_r(x) -> Omega_{r-1}(x)
```

Past-outward record:

```text
R_out,r : present_survivor(x) -> record_{r+1}(x)
```

Compatibility weights:

```text
w_r(omega) >= 0
sum_{omega in Omega_r(x)} w_r(omega) = 1
```

Present survivor:

```text
rho_present(x)
  = C_r( {rho_omega : omega in Omega_r(x)}, {w_r(omega)} )
```

where `C_r` is a finite compression/update map.

The required object order is:

```text
Sigma_r
-> Omega_r
-> compatibility weights
-> inward compression
-> rho_present
-> outward record
```

If shell radius, inward/outward orientation, or `Omega_r` is erased, this layer
has been replaced by a proxy.

Independent sims:

```text
finite shell stack
future-inward compression
past-outward record
possibility-set weighting
compatibility collapse controls
orientation-erased controls
scrambled-Omega controls
```

### Layer 3: Hopf / Projective / Nested Torus Geometry

Unit spinors form `S3`:

```text
S3 = {psi in C^2 : ||psi|| = 1}
```

Phase action:

```text
psi -> exp(i theta) psi
```

Projective spinor base:

```text
CP1 = S3 / U(1)
```

Hopf projection:

```text
pi : S3 -> CP1
pi(psi) = [psi]
```

Hopf connection candidate:

```text
A = -i psi^dagger d psi
```

Nested Hopf torus at fixed `eta`:

```text
T_eta
  = { psi(phi, chi; eta) : phi, chi in [0,2pi) }
  subset S3
```

Fiber loop:

```text
gamma_f(u) = psi(phi_0 + u, chi_0; eta_0)
```

Base-lift loop:

```text
gamma_b(u) = psi(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)
```

Horizontal condition:

```text
A(d gamma_b / du) = 0
```

Why nested Hopf tori belong in the layer stack:

```text
they provide the fiber/base loop geometry on which later Weyl terrain
placements act
```

Independent sims:

```text
S3 unit spinor carrier
CP1 projective spinor base
Hopf projection
fiber loop
base-lift loop
nested Hopf torus family
Clifford torus in S3
horizontal-lift controls
phase-erased controls
```

### Layer 4: Clifford / Quaternion / Spin / Twistor Local Structure

Quaternion:

```text
q = a + b i + c j + d k
||q||^2 = a^2 + b^2 + c^2 + d^2
```

Unit quaternion action:

```text
v' = q v q^{-1}
```

Spin double cover:

```text
Spin(3) ~= SU(2)
SU(2) -> SO(3)
q and -q map to the same SO(3) rotation
```

Clifford algebra:

```text
e_i e_j + e_j e_i = 2 g_ij
```

Gamma relation:

```text
gamma_mu gamma_nu + gamma_nu gamma_mu = 2 eta_{mu nu} I
```

Chirality projector candidate:

```text
gamma5 = i gamma0 gamma1 gamma2 gamma3
P_L = (I - gamma5) / 2
P_R = (I + gamma5) / 2
```

Twistor incidence candidate:

```text
omega^A = i X^{AA'} pi_{A'}
```

This layer is geometry because it constrains the allowed local frame, spin,
orientation, chirality, and incidence structure of the spinor-network cells.

Independent sims:

```text
Cl(3) product relations
Cl(6) product relations
quaternion rotor action
SU(2) double cover
chirality projector consistency
left/right sheet separation
twistor incidence
spinor-to-density bridge controls
```

### Layer 5: Left / Right Weyl Sheet Cover

The manifold must carry two semi-independent Weyl operating spaces.

Objects:

```text
psi_L, psi_R in C^2
||psi_L|| = ||psi_R|| = 1

rho_L = psi_L psi_L^dagger
rho_R = psi_R psi_R^dagger

H_L = +H0
H_R = -H0
```

Sheet dynamics:

```text
d rho_L / dt = -i [H_L, rho_L]
d rho_R / dt = -i [H_R, rho_R]
```

This is not just a sign flip. The valid split also requires:

```text
sink/source swap
distinct left/right dissipative families
distinct retained-strata projectors
distinct loop ownership
distinct terrain basins
```

Independent sims:

```text
left Weyl sheet alone
right Weyl sheet alone
left/right coupled comparison
left/right mirror-collapse negative control
sink/source swap control
loop ownership control
```

### Layer 6: Eight Terrain Generator Laws

"Terrain" is not a label. It means a candidate generator/channel family on one
Weyl sheet.

Let:

```text
D[L](rho)
  = L rho L^dagger
    - 1/2 (L^dagger L rho + rho L^dagger L)
```

There are eight terrain laws:

```text
left sheet:
  Se / Funnel
  Ne / Vortex
  Ni / Pit
  Si / Hill

right sheet:
  Se / Cannon
  Ne / Spiral
  Ni / Source
  Si / Citadel
```

These names do not select a final equation. They bind to candidate generator
families that must be tested.

#### 6.1 Se / Funnel, left sheet

Candidate:

```text
X_F^L(rho_L)
  = sum_k D[L_k^{F,L}](rho_L)
    - i eps_{F,L} [H_L, rho_L]
```

Expected mathematical role:

```text
contractive / focusing / noise-compatible basin generator
```

#### 6.2 Ne / Vortex, left sheet

Candidate:

```text
X_V^L(rho_L)
  = -i [H_L, rho_L]
    + eps_{V,L} sum_k D[M_k^{V,L}](rho_L)
```

Expected mathematical role:

```text
circulating / rotational / order-sensitive basin generator
```

#### 6.3 Ni / Pit, left sheet

Candidate:

```text
sigma_minus = [[0,0],[1,0]]

X_P^L(rho_L)
  = gamma_{P,L} D[sigma_minus](rho_L)
    - i eps_{P,L} [H_L, rho_L]
```

Expected mathematical role:

```text
sink / absorbing / inward basin generator
```

#### 6.4 Si / Hill, left sheet

Candidate:

```text
P_j^{H,L} = P_j^{H,L} P_j^{H,L}
sum_j P_j^{H,L} = I

X_H^L(rho_L)
  = -i [K_L, rho_L]
    + sum_j kappa_{H,L,j}
      (P_j^{H,L} rho_L P_j^{H,L}
       - 1/2(P_j^{H,L} rho_L + rho_L P_j^{H,L}))
```

Expected mathematical role:

```text
barrier / ridge / retained-strata generator
```

#### 6.5 Se / Cannon, right sheet

Candidate:

```text
X_C^R(rho_R)
  = sum_k D[L_k^{C,R}](rho_R)
    - i eps_{C,R} [H_R, rho_R]
```

Expected mathematical role:

```text
outward kick / directed release / right-sheet focusing counterpart
```

#### 6.6 Ne / Spiral, right sheet

Candidate:

```text
X_S^R(rho_R)
  = -i [H_R, rho_R]
    + eps_{S,R} sum_k D[M_k^{S,R}](rho_R)
```

Expected mathematical role:

```text
spiraling / rotating / order-sensitive right-sheet generator
```

#### 6.7 Ni / Source, right sheet

Candidate:

```text
sigma_plus = [[0,1],[0,0]]

X_{So}^R(rho_R)
  = gamma_{So,R} D[sigma_plus](rho_R)
    - i eps_{So,R} [H_R, rho_R]
```

Expected mathematical role:

```text
source / emission / outward basin generator
```

#### 6.8 Si / Citadel, right sheet

Candidate:

```text
P_j^{Ci,R} = P_j^{Ci,R} P_j^{Ci,R}
sum_j P_j^{Ci,R} = I

X_{Ci}^R(rho_R)
  = -i [K_R, rho_R]
    + sum_j kappa_{Ci,R,j}
      (P_j^{Ci,R} rho_R P_j^{Ci,R}
       - 1/2(P_j^{Ci,R} rho_R + rho_R P_j^{Ci,R}))
```

Expected mathematical role:

```text
protected / fortress-like / retained-structure generator
```

#### 6.9 Attractor-Basin Meaning

For each terrain law:

```text
d rho / dt = X_tau^s(rho)
Phi_tau^s(t) = finite-time flow/channel
```

Fixed set:

```text
A_tau^s = {rho : X_tau^s(rho) = 0}
```

Basin:

```text
B_tau^s(A)
  = {rho_0 : limit_{t -> infinity} dist(Phi_tau^s(t)(rho_0), A) = 0}
```

Each of the eight terrain laws must be simulated independently before it is
nested into placements or operator cells.

### Layer 7: Sixteen Terrain Placements On Left/Right Loops

The loop fields come from the Hopf/nested-torus layer.

Four loop carriers:

```text
left inner:  (rho_L, gamma_f^L)
left outer:  (rho_L, gamma_b^L)
right inner: (rho_R, gamma_f^R)
right outer: (rho_R, gamma_b^R)
```

A placement is:

```text
placement = (terrain generator, Weyl sheet, Hopf loop field)
```

General placement map:

```text
d psi_s / dt = Omega_{tau,s,ell} Y_ell^s psi_s
d rho_s / dt = X_{tau,s}(rho_s)

s in {L,R}
ell in {inner, outer}
tau in {Se,Ne,Ni,Si}
```

The sixteen placements are:

```text
(X_F^L,  gamma_f^L)
(X_V^L,  gamma_f^L)
(X_P^L,  gamma_f^L)
(X_H^L,  gamma_f^L)

(X_F^L,  gamma_b^L)
(X_V^L,  gamma_b^L)
(X_P^L,  gamma_b^L)
(X_H^L,  gamma_b^L)

(X_C^R,  gamma_f^R)
(X_S^R,  gamma_f^R)
(X_{So}^R, gamma_f^R)
(X_{Ci}^R, gamma_f^R)

(X_C^R,  gamma_b^R)
(X_S^R,  gamma_b^R)
(X_{So}^R, gamma_b^R)
(X_{Ci}^R, gamma_b^R)
```

This is geometry only if both parts are load-bearing:

```text
Hopf loop field changes the spinor path
terrain generator changes the density/cut/channel behavior
```

If the loop field is erased, the placement is reduced to a channel row. If the
terrain generator is erased, the placement is reduced to a path label.

### Layer 8: Local Operator / Channel Degree-Of-Freedom Maps

Operators are geometric only when they are allowed local actions on the
spinor-network cells.

General object:

```text
End(H_cell) = allowed local endomorphism space
Chan(H_cell) = allowed CPTP channel space
Gen(H_cell) = allowed generator space
```

Candidate local maps:

#### Projector / Pinching Family

```text
{P_a} finite orthogonal projectors
P_a P_b = delta_ab P_a
sum_a P_a = I

Pinch_P(rho) = sum_a P_a rho P_a
```

#### Complementary Projector Family

```text
{Q_b} finite orthogonal projectors
Q_a Q_b = delta_ab Q_a
sum_b Q_b = I

Pinch_Q(rho) = sum_b Q_b rho Q_b
```

Order-sensitive condition:

```text
Pinch_P o Pinch_Q != Pinch_Q o Pinch_P
```

when the projector algebras do not commute.

#### Unitary Transport Family

```text
U(theta) = exp(-i theta A)

Transport_U(rho) = U rho U^dagger
```

#### Local Channel Family

```text
Phi(rho) = sum_a K_a rho K_a^dagger
sum_a K_a^dagger K_a = I
```

#### Lindblad Generator Family

```text
L(rho)
  = -i[H, rho]
    + sum_a D[L_a](rho)
```

These are the actual mathematical candidates. Source shorthand labels may map
onto these families later, but the labels are not used as evidence.

Independent sims:

```text
projector pinching family
complementary projector family
unitary transport family
CPTP channel family
Lindblad generator family
noncommuting order controls
cell-locality controls
```

### Layer 9: Operator-Terrain Local Cells

This is where the deeper local constraint begins. A terrain generator and an
operator/channel act on the same finite local spinor-network cell.

Cell object:

```text
cell z = (c, s, ell, tau, A)

c   = finite site/bond/face/3-cell
s   = L or R sheet
ell = inner or outer loop
tau = one of the eight terrain laws through sheet s
A   = one allowed local operator/channel/generator
```

Two possible compositions:

```text
operator after terrain:
  rho' = A( Phi_tau^s(dt)(rho) )

terrain after operator:
  rho' = Phi_tau^s(dt)( A(rho) )
```

N01 witness:

```text
A o Phi_tau^s != Phi_tau^s o A
```

The local-cell layer is not a schedule table. A cell is admissible only if it
has:

```text
finite carrier cell
Weyl sheet
Hopf loop placement
terrain generator
operator/channel map
order-sensitive control
QIT readout if a cut/state exists
```

Independent sims:

```text
one operator family against one terrain law
one terrain law against one operator family
all eight terrain laws individually
all sixteen placements individually
operator-terrain order controls
cell-locality ablations
```

### Layer 10: Ordered Cycle / Ratchet Paths

Only after local cells exist can ordered paths be tested.

Finite word:

```text
W = (z_1, z_2, ..., z_T)
```

where each `z_i` is an admitted local operator-terrain cell.

Path map:

```text
R_W = Phi_{z_T} o ... o Phi_{z_2} o Phi_{z_1}
```

Order test:

```text
R_W(rho_0) != R_{W'}(rho_0)
```

where `W'` is a valid order permutation or order-erased control.

Ratchet condition:

```text
survivor_set(R_W) != survivor_set(R_{W'})
```

or:

```text
Q_P(R_W(M(C))) != Q_P(R_{W'}(M(C)))
```

This is the first place where "ratchet" can become a tested mathematical
object instead of a name.

### Layer 11: Gluing / Groupoid / Equivariant Closure

This is a stacking/closure layer, not a starting layer.

Finite groupoid:

```text
G = (Obj, Arr, s, t, inv, comp)

s(g) = source object
t(g) = target object
h o g defined iff t(g) = s(h)
```

Associativity:

```text
k o (h o g) = (k o h) o g
```

Identity:

```text
id_x o g = g
g o id_y = g
```

Finite gluing:

```text
cover = {U_i}
sections a_i in F(U_i)

a_i |_{U_i cap U_j} = a_j |_{U_i cap U_j}
```

Global section question:

```text
exists a in F(union_i U_i)
such that a|_{U_i} = a_i
```

Equivariance:

```text
f(g.x) = g.f(x)
```

This layer asks whether local pieces compose into coherent finite geometry.
It cannot be claimed from graph connectivity or a row inventory.

## 8. Entropy And QIT Readouts Across Every Layer

Entropy is not a low layer. It is a readout that runs wherever the needed
state, cut, channel, path, or shell exists.

### 8.1 State Entropy

Von Neumann entropy:

```text
S(rho) = -Tr(rho log rho)
```

Renyi entropy:

```text
S_alpha(rho)
  = (1 / (1 - alpha)) log Tr(rho^alpha)
```

Second Renyi entropy:

```text
S_2(rho) = -log Tr(rho^2)
```

Purity:

```text
Purity(rho) = Tr(rho^2)
```

Linear entropy:

```text
S_L(rho) = 1 - Tr(rho^2)
```

### 8.2 Bipartite Cut Readouts

For:

```text
rho_AB in D(H_A tensor H_B)
rho_A = Tr_B(rho_AB)
rho_B = Tr_A(rho_AB)
```

Entanglement entropy for a pure global state:

```text
S_ent(A) = S(rho_A) = S(rho_B)
```

Mutual information:

```text
I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)
```

Conditional entropy:

```text
S(A|B) = S(rho_AB) - S(rho_B)
```

Coherent information:

```text
I_c(A -> B) = S(rho_B) - S(rho_AB)
            = -S(A|B)
```

Relative entropy:

```text
D(rho || sigma) = Tr rho (log rho - log sigma)
```

Logarithmic negativity:

```text
E_N(rho_AB) = log || rho_AB^{T_B} ||_1
```

Entanglement spectrum:

```text
Spec_ent(A) = eigenvalues(rho_A)
```

### 8.3 Channel And Process Readouts

Channel output entropy:

```text
S(Phi(rho))
```

Entropy production:

```text
Delta S = S(Phi(rho)) - S(rho)
```

Process/history probability:

```text
p(h) = Tr(K_h rho K_h^dagger)
```

Path entropy:

```text
H_path = - sum_h p(h) log p(h)
```

### 8.4 Shell Readouts

Shell possibility entropy:

```text
H_Omega(r,x)
  = - sum_{omega in Omega_r(x)}
      w_r(omega) log w_r(omega)
```

Boundary entropy:

```text
S_B(r,x) = S(rho_{B_r})
```

Binding/correlation readout:

```text
K_binding(r,x) in {
  I(A_r:B_r),
  I_c(A_r -> B_r),
  -S(A_r|B_r),
  E_N(rho_{A_r B_r}),
  D(posterior || prior)
}
```

The unique shell gradient is not ordinary scalar entropy:

```text
Delta_r H_Omega
Delta_r S_B
Delta_r K_binding
```

Axis0 can later read this polarity. The entropy readout itself is not Axis0.

## 9. Flux As Derived Terrain/Transport Current

Flux is not primitive. It is a derived current over already-built carrier,
terrain, transport, and cut objects.

Let `q_v(t)` be a local readout on site/cell `v`:

```text
q_v(t) in {
  S(rho_v),
  I(A_v:B_v),
  I_c(A_v -> B_v),
  H_Omega(r,v),
  terrain-potential value,
  compatibility weight
}
```

Edge current:

```text
J_e^q(t) = current of q across edge e
```

Discrete continuity equation:

```text
Delta_t q_v + div_K J^q(v) = sigma_v
```

where:

```text
sigma_v = local source/sink term from terrain or channel action
```

Flux cannot be separated from terrain if terrain dynamics define the
source/sink/current. It is downstream because the carrier and local dynamics
must exist first.

## 10. Xi, Phi0, Axis0

Axis0 is not an individual geometry layer. It is a downstream polarity readout
over the shell/spinor/cut/history object.

Shell bridge:

```text
Xi_shell:
  (Sigma_r, Omega_r, inward/outward orientation,
   spinor-network carrier, path family)
  -> rho_AB or rho_{I_r B_r}
```

Raw Axis0 vector candidate:

```text
A0_raw(r,x)
  = (
      Delta_r H_Omega(r,x),
      Delta_r S_B(r,x),
      Delta_r K_binding(r,x),
      order_gap(r,x),
      chirality_sheet(r,x)
    )
```

Projection candidate:

```text
Phi0(A0_raw) -> expansion-dominant or binding-dominant
```

The projection must be discovered or tested. It must not be assumed.

Positive/allostatic face:

```text
future possibility set opens
shell entropy expands
branchability grows
space/time/dark-energy-like expression in the model
```

Negative/homeostatic face:

```text
future possibility set converges
correlation is preserved
information binds
gravity/dark-matter-like expression in the model
```

This section states the target consumer shape. It does not prove physics.

## 11. FEP / Holodeck As Consumer Math

FEP is not imported source ontology. In this program it is a later predictive
consumer over admitted QIT/shell objects.

Finite history:

```text
h = (a_1, ..., a_T)
K_h = K_{a_T} ... K_{a_1}
```

Evidence:

```text
Z_path
  = sum_h Tr( E K_h rho K_h^dagger )
```

Posterior:

```text
tau = sum_h E K_h rho K_h^dagger E^dagger
rho_post = tau / Tr(tau)
```

Quantum free-energy-style readout:

```text
F_Q(sigma)
  = D(sigma || rho_post) - log Z_path
```

Connection to the model:

```text
future possibility shell = prediction family
boundary/probe/evidence = constraint
posterior/survivor = compressed present
outward record = memory/history surface
```

This can run at many layers as a readout/consumer. It does not replace the
layer math.

## 12. G-Structure Candidates

A G-structure is a frame/bundle reduction. It is not one of the manifold
layers.

Continuum form:

```text
Fr(M) -> M = frame bundle
G subset GL(n,R)
P_G subset Fr(M)
```

Finite analog:

```text
F_K = finite frame/carrier set over K
I_G = invariant tensor/form/spinor/bundle data

F_G = {f in F_K : f preserves I_G}
```

Each candidate below must be simulated independently before it can be used as
the frame structure for stacking.

### 12.1 U(1)

```text
U(1) = {exp(i theta)}
psi -> exp(i theta) psi
```

Use:

```text
Hopf fiber phase
connection A
holonomy integral over loop
```

### 12.2 SU(2) / Spin(3)

```text
SU(2) = {U in C^{2x2} : U^dagger U = I, det U = 1}
Spin(3) ~= SU(2)
```

Use:

```text
unit spinors
quaternion rotors
double cover of SO(3)
```

### 12.3 SO(3)

```text
SO(3) = {R in R^{3x3} : R^T R = I, det R = 1}
```

Use:

```text
orientation frame reduction
```

Reflection controls with `det = -1` must fail if orientation is load-bearing.

### 12.4 Pin / Spin

```text
Spin(n) double-covers SO(n)
Pin(n) double-covers O(n)
```

Use:

```text
spin lifts
reflection controls
chirality split
```

### 12.5 Spin^c

```text
Spin^c(n) = (Spin(n) x U(1)) / {(-1, -1)}
```

Use:

```text
spin structure plus U(1) phase/line-bundle coupling
```

### 12.6 Symplectic Structure

```text
J^T = -J
det J != 0

Sp(2n,R) = {M : M^T J M = J}
```

Use:

```text
Hamiltonian flow
phase-space-like order-sensitive dynamics
```

### 12.7 Almost Complex / Kahler Structure

Almost complex:

```text
J^2 = -I
```

Kahler compatibility:

```text
g(JX,JY) = g(X,Y)
omega(X,Y) = g(JX,Y)
d omega = 0
```

Use:

```text
projective Hilbert geometry
Berry/Fubini-Study-style metric readouts
```

### 12.8 SU(n) / Calabi-Yau Type Structure

```text
holonomy subset SU(n)
```

Candidate invariant data:

```text
omega = Kahler form
Omega = holomorphic volume form
d omega = 0
d Omega = 0
```

Use:

```text
complex volume-preserving geometry candidate
```

### 12.9 G2 Structure

On a 7-dimensional real carrier:

```text
phi = stable 3-form
g_phi = metric induced by phi
```

Torsion-free ideal:

```text
d phi = 0
d *phi = 0
```

Use:

```text
exceptional 7D geometry candidate
```

### 12.10 Spin(7) Structure

On an 8-dimensional real carrier:

```text
Psi = Cayley 4-form
```

Torsion-free ideal:

```text
d Psi = 0
```

Use:

```text
exceptional 8D geometry candidate
```

### 12.11 Seiberg-Witten-Style Gauge/Spinor Candidate

Standard 4D schematic form:

```text
D_A psi = 0
F_A^+ = q(psi)
```

Eight-dimensional variants are not one canonical equation here. They should be
treated as gauge/spinor coupled candidates:

```text
Dirac-type spinor equation
curvature projection equation
finite gauge-field control
finite spinor-network carrier
```

Use:

```text
test whether gauge curvature plus spinor constraints are useful for the stack
```

### 12.12 Hybrid Candidate

The likely useful structure may be a hybrid rather than one named structure.

Finite hybrid object:

```text
Hyb_K
  = (
      U(1) Hopf phase data,
      SU(2)/Spin spinor data,
      Clifford module data,
      shell possibility data,
      terrain/operator local action data,
      gluing/groupoid data
    )
```

Selection criterion:

```text
Hyb_K is useful only if it preserves more of the required layer data
than the named alternatives under the same controls.
```

## 13. Other Geometry Objects To Sim Independently

These are not all G-structures. They are geometry objects, algebraic
structures, or alternative carriers that should be tested beside the layer
stack.

```text
S3 unit spinor carrier
CP1 projective spinor base
Hopf fibration S3 -> CP1
nested Hopf tori T_eta
Clifford torus
twistor incidence geometry
finite Clifford module geometry Cl(3), Cl(6)
quaternionic projective variants
finite spectral triple
finite cell complex
simplicial/cubical complex topology
persistent homology filtration
finite contextuality/sheaf geometry
finite projective designs
finite effect/POVM geometries
quantum comb / process POVM histories
contact geometry candidate
information-metric geometry candidate
Grassmannian / flag manifold candidates
Dirac monopole / Chern class candidate
higher Hopf fibration candidates
gauge/spinor coupled candidates
```

Each gets its own standalone sim before official stacking.

## 14. What Must Be Simulated Before Stacking

Independent layer sims:

```text
L0 finite response quotient
L1 source-native spinor network
L2 shell possibility field
L3 Hopf/nested-torus geometry
L4 Clifford/quaternion/spin/twistor local structure
L5 left/right Weyl sheet cover
L6 each of the eight terrain generators
L7 each of the sixteen terrain placements
L8 each local operator/channel candidate family
L9 operator-terrain local cell compositions
L10 ordered cycle/ratchet paths
L11 gluing/groupoid/equivariant closure
```

Independent geometry and G-structure sims:

```text
S3
CP1
Hopf fibration
nested Hopf tori
Clifford torus
twistor incidence
Cl(3)
Cl(6)
quaternion rotors
U(1)
SU(2)/Spin(3)
SO(3)
Pin/Spin
Spin^c
symplectic
almost complex/Kahler
SU(n)/Calabi-Yau type
G2
Spin(7)
Seiberg-Witten-style gauge/spinor candidates
hybrid Hopf-spin-twistor-Clifford reductions
```

Independent readout sims:

```text
state entropy
cut entropy
mutual information
conditional entropy
coherent information
relative entropy
log negativity
entanglement spectrum
path entropy
shell possibility entropy
boundary entropy
binding/correlation readouts
```

Only after those exist should composition tests begin:

```text
A then B versus B then A
layer subset nesting
valid order cycles
survivor quotient under stacked constraints
groupoid/gluing closure
derived flux current
Xi/Phi0/Axis0 consumers
FEP/Holodeck consumers
physics/gravity-model alignment consumers
```

## 15. Standard For A Full Sim

A full sim of one layer must not be a toy, a scout label, or a shared wrapper
with a renamed invariant.

Minimum standard:

```text
one layer per executable sim
source-native spinor-network carrier where relevant
finite site/bond/face/cell locality
dynamic update, not only static invariant
MPS/PEPS2D/PEPS3D representation or explicit blocker where relevant
QIT entropy/cut/channel/path readouts when inputs exist
controls that weaken or kill the claim
tool ablations with outcome deltas
fresh rerun receipt
blocked downstream consumers listed
no promotion from scout to admitted layer without a separate gate
```

Numerical/tool roles:

```text
PyTorch:
  primary complex spinor/density/autograd engine where required

JAX:
  independent numeric/dynamics/parity engine where useful

MPS/PEPS2D/PEPS3D tooling:
  contraction representations of the spinor network, not ontology

quimb/cotengra/opt_einsum/autoray:
  tensor-network contraction and path optimization surfaces

Clifford:
  geometric algebra and spinor/rotor checks

SymPy:
  exact symbolic identities

z3/cvc5:
  finite structural constraints, noncommutation, impossibility, or controls

PyG / jraph:
  graph-structured finite carrier dynamics

rustworkx / XGI / TopoNetX / GUDHI:
  graph, hypergraph, cell-complex, and topological checks

e3nn / e3nn-jax:
  equivariant representation checks where symmetry is load-bearing
```

## 16. Final Mathematical Summary

The candidate program is:

```text
F01 finite carrier/probe/operator/path
+ N01 noncommuting or order-sensitive action

-> finite response quotient
-> source-native dynamic spinor network
-> literal shell possibility field
-> Hopf/nested-torus loop geometry
-> Clifford/quaternion/spin/twistor local structure
-> left/right Weyl sheet cover
-> eight terrain generator laws
-> sixteen terrain placements
-> local operator/channel degree-of-freedom maps
-> operator-terrain local cells
-> ordered cycle/ratchet paths
-> gluing/groupoid/equivariant closure

with entropy and QIT readouts running across every layer where valid,
G-structure candidates tested beside the stack,
and flux/Xi/Phi0/Axis0/FEP/physics kept downstream until their inputs exist.
```
