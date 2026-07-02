# Full Nuanced Model Manual

Status: long-form working manual, not canon, not an admission receipt.

This file exists because the first pass of this pack was too shallow. It named
the gates and the repair order, but it did not lay out the actual model with
enough nuance to teach or audit it. This manual keeps the control boundaries,
then expands the objects themselves: what they are, what they are not, how each
one constrains the next, which parts are source math, which parts are runtime
scaffold, and which parts remain blocked.

The goal is not to freeze a canonical layer stack. The goal is to prevent
future agents from flattening distinct degrees of freedom into one smooth story.

## 0. The Central Correction

The old failure was not only that a few terms were wrong. The failure was that
different kinds of objects were being stacked as if they were all the same
thing:

```text
root constraint
quotient rule
carrier
chart
readout
generator
operator
schedule row
tensor-network realization
derived current
Axis0 readout
physics doctrine
Holodeck memory model
```

Those are not interchangeable manifold layers. They are different roles inside
one constraint-admissibility program.

The corrected doctrine is:

```text
First:  finite operational distinguishability under noncommuting operations.
Then:   finite effect/probe response assignments and quotient identity.
Then:   finite PEPS3D-carried spinor-network carrier.
Then:   spinor, Hopf, Weyl, terrain, loop, and operator maps on that carrier.
Then:   operator substages as finite cell/channel/tensor actions.
Then:   flux only as a derived quaternionic/chiral current candidate.
Then:   Xi/Phi0/Axis0 only as downstream cut/history/feedback readouts.
Then:   Holodeck/FEP/physics only as later candidate interpretations.
```

Short version:

```text
do not let a readout become the root
do not let a chart become the manifold
do not let a schedule become geometry
do not let flux become Axis0
do not let Axis0 become the i scalar
do not let Holodeck become proof of cognition or physics
```

## 1. Object Taxonomy

Use this table before calling anything a "layer."

| Role | Example | What it does | What it cannot do by itself |
|---|---|---|---|
| root constraint | `F01`, `N01` | sets the admissibility rules | does not name a carrier or physics object |
| quotient/admission rule | `s1 ~_P s2` | defines identity relative to finite probes | does not prove Hilbert, spinor, Hopf, PEPS3D, or Axis0 |
| finite probe/effect family | SIC/POVM, MUB, process POVM | makes finite responses and finite distinguishability explicit | does not make Bloch/density the root |
| noncommuting algebra | Weyl-Heisenberg `XZ = omega ZX` | witnesses order sensitivity | does not prove engine dynamics |
| carrier | finite Hilbert/spinor/PEPS3D object | gives state/action substrate | does not prove a later readout |
| chart | Bloch, Hopf coordinates, torus coordinate | gives a readable coordinate or projection | is not the manifold root |
| readout | density, entropy, coherent information | measures something about a carrier/cut | cannot replace the carrier |
| generator | terrain law `X_(tau,s)` | defines local flow/channel family | is not a stage or schedule by itself |
| operator | `Ti`, `Te`, `Fi`, `Fe` channel | acts on local state | is not a terrain or Axis0 |
| placement | `(sheet, loop, terrain, operator, sign)` | binds generator, loop, sheet, token, and sign | is not proven by labels alone |
| schedule | IGT/Jung/I Ching row | indexes stage order and signed tokens | is not geometry unless cells/actions are attached |
| tensor realization | MPS/PEPS/PEPS3D | carries local tensors and contractions | local carrier evidence is not full environment theorem |
| derived current | `J_flux = i J_i + j J_j + k J_k` | candidate flux over lower geometry | not Axis0, not physics |
| cut bridge | `Xi: history -> rho_AB` | maps history/geometry into cut state | still open |
| Axis0 readout | `Phi0(rho_AB)`, polarity, many-futures | downstream feedback/cut/history measure | not root, not single scalar closure |
| Holodeck | predictive world/reconstruction loop | candidate memory/perception architecture | not implemented proof or physics |

The same word can appear in more than one role if the exact map changes. For
example, "Axis0" can mean terrain-square polarity, torus-seat diagnostic,
cut-state functional, feedback polarity, or owner i-scalar genealogy. A sim must
name which one it is testing.

## 2. Root Geometry: Finite Distinguishability

The first geometry allowed by the root constraints is a finite quotient geometry.
It is not a Bloch sphere and not a spinor yet.

```text
S = finite admissible state/configuration set
P = finite admitted probe/effect family

s1 ~_P s2 iff for every p in P, p(s1) = p(s2)

Q_P = S / ~_P
```

This is already geometry because it determines which differences are visible,
which points are identified, and which operations can change the quotient.

The two roots constrain it:

```text
F01:
  |S| finite
  |P| finite
  finite operators
  finite histories
  finite carrier dimension

N01:
  A o B != B o A in general
  A rho != rho A in general
  probe identity may depend on order
```

The first admissible "space" is therefore:

```text
M(C) = {x in S : x satisfies active constraint set C}
```

where `C` includes finite probe/effect rules and finite composition rules.
Axes are later readout maps:

```text
A_i : M(C) -> V_i
```

They are not primitive substances.

## 3. Finite Effects: Why The Carrier Cannot Be A Picture

The finite-effect repair exists to stop a visual or matrix representation from
becoming the substrate.

Finite effects:

```text
E = {E_i}
0 <= E_i <= I
sum_i E_i = I

p_i(rho) = Tr(E_i rho)
```

Identity becomes active-probe-relative:

```text
a ~_E b iff every active effect in E gives the same response on a and b
```

The current finite-effect scout supports:

```text
finite SIC effect family
finite SIC response assignment
quotient identity under active probes
global phase quotient
Weyl-Heisenberg noncommutation in d=2 and d=3
MUB as secondary finite probe candidate
finite effect algebra laws
```

The graveyards matter as much as the positives:

```text
single probe identity rejected
commuting operator family rejected as N01 witness
one two-outcome basis rejected as insufficient
arbitrary effect addition rejected
negative effect rejected
unlabeled response rejected
```

The nuance:

```text
finite effect responses can reconstruct or adapt into density matrices
density matrices are useful after this gate
density matrices are not the root object
```

This is why "are density matrices used?" has a nuanced answer:

```text
yes, as torch-native spinor-derived readouts/carriers after finite admission
no, not as the first root geometry
no, not as a replacement for spinor/Hopf information when that information is
load-bearing
```

## 4. The Hilbert/Density Adapter

The local working Hilbert carrier is:

```text
H = C^2
D(H) = {rho in B(H): rho = rho^dagger, rho >= 0, Tr(rho)=1}

rho =
  [[a, u - i v],
   [u + i v, d]]

a,d,u,v real
a + d = 1
u^2 + v^2 <= a d
```

This is a powerful adapter because finite effects and channels can be expressed
cleanly on it. But it is not enough for the new manifold work because density
can erase spinor distinctions.

The Bloch chart:

```text
rho = 1/2(I + r_x sigma_x + r_y sigma_y + r_z sigma_z)
```

is a chart/readout. It is not the manifold root. The classical leakage was
letting the Bloch image look like the object itself. The repair is to keep the
spinor carrier explicit and treat the Bloch vector as a projected diagnostic.

## 5. Spinor Space Is Load-Bearing

The spinor carrier is:

```text
psi_s(phi, chi; eta) =
  [ exp(i(phi + chi)) cos eta,
    exp(i(phi - chi)) sin eta ]^T

s in {L, R}
eta in [0, pi/2]
phi, chi in [0, 2pi)
||psi_s|| = 1
```

Density is derived:

```text
rho_s = psi_s psi_s^dagger

rho_s(phi, chi; eta) =
  [[cos^2 eta, exp(2i chi) cos eta sin eta],
   [exp(-2i chi) cos eta sin eta, sin^2 eta]]
```

Bloch readout:

```text
r_s = (
  sin(2 eta) cos(2 chi),
  sin(2 eta) sin(2 chi),
  cos(2 eta)
)
```

The carrier has more structure than the readout. The fiber coordinate can move
without changing density. That is the basic reason Bloch spheres were demoted:
they see the projected density-visible base, not the whole spinor/Hopf carrier.

## 6. Hopf Tori And The Density Visibility Split

The nested Hopf-torus family:

```text
T_eta^s = {psi_s(phi, chi; eta): phi, chi in [0, 2pi)}
```

Hopf connection:

```text
A = -i psi_s^dagger d psi_s
  = d phi + cos(2 eta) d chi
```

Two loop fields:

```text
Y_in psi_s = partial_phi psi_s

Y_out psi_s =
  (-cos(2 eta) partial_phi + partial_chi) psi_s
```

Inner/fiber loop:

```text
gamma_in^s(u) = psi_s(phi_0 + u, chi_0; eta_0)
rho_in^s(u) = rho_s(phi_0, chi_0; eta_0)
```

Outer/base-lift loop:

```text
gamma_out^s(u) =
  psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)

A(dot gamma_out^s) = 0
rho_out^s(u) changes through chi_0 + u
```

This is a major model distinction:

```text
inner/fiber = spinor motion that can be density-hidden
outer/base = spinor motion that is density-visible
```

If a sim only sees density, it may think the inner/fiber loop did nothing. That
is not proof the loop is absent. It means the readout cannot see that component.

## 7. Left/Right Weyl Sheets

The Weyl split is not two arbitrary copies. It flips the Hamiltonian sign:

```text
H_0 = n_x sigma_x + n_y sigma_y + n_z sigma_z

H_L = +H_0
H_R = -H_0

rho_dot_L = -i[H_L, rho_L]
rho_dot_R = -i[H_R, rho_R]
```

Equivalently, in Bloch-readout language:

```text
rho_dot_L -> +2 n x r_L
rho_dot_R -> -2 n x r_R
```

The Bloch form is only a readout here. The actual requirement is that left and
right sheet behavior survive controls on the spinor/Hopf carrier.

## 8. Quaternion Structure

The spinor carrier has a quaternion reading:

```text
S^3 = SU(2) = unit quaternions
```

Quaternion basis:

```text
i^2 = j^2 = k^2 = i j k = -1
i j = k
j k = i
k i = j
j i = -k
k j = -i
i k = -j
```

A valid quaternion use needs a map or invariant:

```text
psi_v = (z_1, z_2)
q_v = z_1 + j z_2

I_q(v,w) = q_v^{-1} q_w
```

or another explicit finite invariant.

The nuance:

```text
quaternion structure is real carrier geometry
quaternion naming is not enough
the i scalar is not the whole quaternion story
j/k cannot be erased if the owner model needs future/past fuzz or shell boundary
```

The current IJK flux row is useful because it gates literal quaternion units and
keeps `i,j,k` as pure quaternion coefficients. It is still a formal scout, not
final flux or Axis0.

## 9. PEPS3D From The First Carrier Step

PEPS3D is not an afterthought. In new manifold work, it is the finite
spinor-network carrier from the first admitted carrier step:

```text
K = (V, E, F, C)

V = finite sites
E = finite bonds
F = finite faces or boundary patches
C = finite cells or substage-cell anchors
```

Local site:

```text
psi_(v,s) in C^2
||psi_(v,s)|| = 1

p_(v,a) = <psi_(v,s)| E_a |psi_(v,s)>
```

Local tensor:

```text
T_v[
  alpha_x_minus,
  alpha_x_plus,
  alpha_y_minus,
  alpha_y_plus,
  alpha_z_minus,
  alpha_z_plus,
  a
]
```

where `a` is the finite physical/probe/spinor index and `alpha_*` are finite
virtual bond indices.

For an edge:

```text
e = (u,v)
transport = U_(uv,s) or channel Phi_(uv,s)

N01 witness:
  Phi_(uv) o Phi_(vw) != Phi_(vw) o Phi_(uv)
```

For a shell/boundary:

```text
Shell_k = finite set of sites/faces with q_shell(k)
R_alpha(Psi_s, boundary, engine, shell)
alpha in {i,j,k}
```

Readout:

```text
boundary reduced response = finite contraction of boundary tensors
```

Not allowed as final evidence:

```text
dense 2**64 closure except fenced smoke/control
scalar PEPS3D label
PEPS3D introduced only after stage labels
random PEPS tensor with no source spinor/effect/probe anchor
```

## 10. MPS, PEPS, PEPS3D: What The Current Receipts Mean

The current suite has real tensor-network pressure, but the ceilings differ.

Useful current receipts include:

```text
explicit spinor MPS scale at 8/16/32/64 sites
explicit spinor PEPS3D local tensor carrier at 4x4x4 = 64 sites
MPS vs PEPS vs PEPS3D comparison rows
source-native 32/64-site PEPS3D capacity rows
subdense local-environment contractions
PEPS3D contraction-order boundary witness
PEPS3D substrate quotient distinguishability witness
```

What they do support:

```text
bounded formal-scout tensor evidence
explicit spinor transport through some MPS/PEPS/PEPS3D carriers
controls against flattened/wrong-adjacency/scalar/zero substitutes in narrow rows
```

What they do not support:

```text
full PEPS3D environment theorem
long-horizon engine convergence
final flux
Axis0 theorem
physics
```

This distinction has to stay in the docs. A green suite is not a manifold proof.

## 11. Terrain Generators

Terrain is the generator family. Loop is the spinor path field. Placement is
generator plus loop plus sheet plus schedule role.

Four terrain families:

```text
Se = dissipative outward/open family
Ne = Hamiltonian circulation/noncommuting family
Ni = dissipative inward/contracting family
Si = stratified/commuting Hamiltonian plus invariant subspaces
```

Eight chiral terrain realizations:

```text
Type 1 / L:
  Se = Funnel
  Ne = Vortex
  Ni = Pit
  Si = Hill

Type 2 / R:
  Se = Cannon
  Ne = Spiral
  Ni = Source
  Si = Citadel
```

Dissipator:

```text
D[L](rho) = L rho L^dagger - 1/2(L^dagger L rho + rho L^dagger L)
```

Terrain generators from the source terrain packet:

```text
X_Se,L(rho) =
  lambda_Se,L sum_j D[sigma_j](rho) - i eps_Se,L [H_L, rho]

X_Se,R(rho) =
  lambda_Se,R sum_j D[sigma_j](rho) - i eps_Se,R [H_R, rho]

X_Ne,L(rho) =
  -i[H_L, rho]

X_Ne,R(rho) =
  -i[H_R, rho]

X_Ni,L(rho) =
  gamma_Ni,L D[sigma_-](rho) - i eps_Ni,L [H_L, rho]

X_Ni,R(rho) =
  gamma_Ni,R D[sigma_+](rho) - i eps_Ni,R [H_R, rho]

X_Si,L(rho) =
  -i[omega_L m_L.sigma, rho]
  + kappa_L(P_+^L rho P_+^L + P_-^L rho P_-^L - rho)

X_Si,R(rho) =
  -i[omega_R m_R.sigma, rho]
  + kappa_R(P_+^R rho P_+^R + P_-^R rho P_-^R - rho)
```

The terrain-square wording that must survive:

```text
A0+ / N-side = {Ne, Ni}
A0- / S-side = {Se, Si}
```

This is not final Axis0. It is a native terrain polarity that later Axis0
readouts must preserve, test, or explicitly explain away.

## 12. Placement Counts

Counts that must not be confused:

```text
terrain families = 4
  {Se, Ne, Ni, Si}

terrain realizations = 8
  {(Se,L), (Ne,L), (Ni,L), (Si,L),
   (Se,R), (Ne,R), (Ni,R), (Si,R)}

terrain-loop placements = 16
  {(tau, s, ell):
     tau in {Se,Ne,Ni,Si},
     s in {L,R},
     ell in {inner/fiber, outer/base}}
```

The explicit placement has both a spinor law and density law:

```text
placement(tau,s,ell):
  psi_dot_s = Omega_(tau,s,ell) Y_ell psi_s
  rho_dot_s = X_(tau,s)(rho_s)
```

That pair matters. If only the density law is present, the sim may miss the
spinor loop distinction. If only the label is present, there is no placement.

## 13. Operator Families

The intrinsic operator math is the four operator families. `UP` and `DOWN` are
not extra operators; they appear only after terrain/placement is chosen.

State:

```text
rho =
  [[a, u - i v],
   [u + i v, d]]
```

### Ti

`Ti` is the z-basis dephasing/pinching channel:

```text
P_0 = (I + sigma_z)/2
P_1 = (I - sigma_z)/2

Ti_q(rho) =
  (1-q) rho + q(P_0 rho P_0 + P_1 rho P_1)

= [[a, (1-q)(u - i v)],
   [(1-q)(u + i v), d]]
```

Continuous generator:

```text
L_Ti(rho) = (kappa/2)(sigma_z rho sigma_z - rho)
```

### Te

`Te` is the x-basis dephasing/pinching channel:

```text
Q_+ = (I + sigma_x)/2
Q_- = (I - sigma_x)/2

Te_q(rho) =
  (1-q) rho + q(Q_+ rho Q_+ + Q_- rho Q_-)
```

The pinched x-basis component is:

```text
Q_+ rho Q_+ + Q_- rho Q_- =
  [[1/2, u],
   [u, 1/2]]
```

### Fi

`Fi` is a coherent x-rotation:

```text
U_x(theta) =
  [[cos(theta/2), -i sin(theta/2)],
   [-i sin(theta/2), cos(theta/2)]]

Fi_theta(rho) = U_x(theta) rho U_x(theta)^dagger
```

In coordinates:

```text
a' = a cos^2(theta/2) + d sin^2(theta/2) + v sin(theta)
d' = a sin^2(theta/2) + d cos^2(theta/2) - v sin(theta)
u' = u
v' = v cos(theta) - ((a-d)/2) sin(theta)
```

### Fe

The read-only operator packet gives `Fe` as a coherent z-rotation:

```text
U_z(phi) =
  [[exp(-i phi/2), 0],
   [0, exp(i phi/2)]]

Fe_phi(rho) = U_z(phi) rho U_z(phi)^dagger
```

Output:

```text
[[a,
  (u cos phi - v sin phi) - i(u sin phi + v cos phi)],
 [(u cos phi - v sin phi) + i(u sin phi + v cos phi),
  d]]
```

Current mismatch:

```text
canonical_qit_engine_specs.py maps Fe to sigma_y
operator math packet maps Fe to z-rotation
one 64-substage scout used Fe as sigma_z in local operator_matrix
```

Until this is reconciled, docs may preserve the four-slot grammar but must not
claim final Fe dynamics.

## 14. Operators Are Not Geometry Until They Are Cell Actions

This answers the recurring substage question directly.

The four substages are different operators. They are not automatically separate
geometries. They become geometric only when each operator is realized as a
finite action on the already-built carrier:

```text
cell c = (engine_type, macro_stage, loop_field, terrain, operator_slot)

T_c = finite PEPS3D-carried local tensor/channel/action
```

A valid substage cell must contain:

```text
finite PEPS3D site/bond/face/cell anchor
spinor/Hopf/Weyl local state or projection from richer carrier
finite probe/effect response
operator/channel/tensor update
Axis6 order witness
negative/control
blocked downstream consumers
```

So the operator does not "emerge" as a new substance. It emerges, if earned, as
an admissible endomorphism/channel/tangent action on the constrained carrier.

Better wording:

```text
operators are local admissible actions over the manifold carrier
substage geometry is the cell/action bundle over stage placement
operator labels alone are not cells
64 operator rows alone are not manifold closure
```

## 15. IGT, Jung, I Ching, And The 64 Schedule

The schedule atlas has a governing split:

```text
IGT:
  stage grammar
  WIN / LOSE / win / lose
  same-sign vs mixed
  outer/inner
  first/second asymmetry

Jung:
  operator pair tokens
  loop families
  signed operators

I Ching:
  64-slot schedule index
  optional indexing surface
```

They do not redefine each other.

The full mapping is not reproduced in this section. Use
`06_FULL_IGT_MAPPING_ATLAS.md` for the complete quadrant table, ordered-token
law, signed-operator variants, Type-1 and Type-2 charts, 8x8 schedule grid, and
the runtime 64 substage expansion.

Signed operators:

```text
UP = operator first
DOWN = terrain first
Phi_T o U_O != U_O o Phi_T in general
```

Ordered token examples:

```text
TiSe vs SeTi
FiNe vs NeFi
TeNi vs NiTe
FeSi vs SiFe
```

`UP/DOWN` is not an operator. It is composition order after the terrain map is
chosen.

## 16. Type 1 And Type 2 Engine Tables

Type 1 / left:

| Topology | Outer token | Outer op | Outer A6 | Inner token | Inner op | Inner A6 |
|---|---|---|---|---|---|---|
| Se | TiSe | Ti | up | SeFi | Fi | down |
| Ne | NeTi | Ti | down | FiNe | Fi | up |
| Ni | NiFe | Fe | down | TeNi | Te | up |
| Si | FeSi | Fe | up | SiTe | Te | down |

Type 2 / right:

| Topology | Outer token | Outer op | Outer A6 | Inner token | Inner op | Inner A6 |
|---|---|---|---|---|---|---|
| Se | FiSe | Fi | up | SeTi | Ti | down |
| Ne | NeFi | Fi | down | TiNe | Ti | up |
| Ni | NiTe | Te | down | FeNi | Fe | up |
| Si | TeSi | Te | up | SiFe | Fe | down |

The same four topology families appear, but engine type changes:

```text
sheet
loop placement
operator
token order
Axis6 sign
stage result
```

Those are distinct degrees of freedom. They can correlate, but correlation is
not collapse.

## 17. The 64-Substage Target

Current grammar:

```text
2 engine types
x 8 macro stages per engine
x 4 operator substages per macro stage
= 64 substages
```

The present scaffold has evidence for grammar/count pressure:

```text
engine count = 2
macro-stage count = 16
substage count = 64
terrain variants = 8
topology count = 4
operator count = 4
controls reject mixed-Axis6, native-only collapse, one-engine collapse
```

But the repair audit blocks overclaim:

```text
16 stage sites + 4 operator rows per site
!= 64 PEPS3D manifold cells
```

The real target is:

```text
64 finite PEPS3D-carried cells
each with local spinor/Hopf position
each with a tensor/channel action
each with order witness
each with controls
```

Until that exists, the 64 schedule is a source-conformant scaffold and formal
scout target, not final manifold geometry.

## 18. Flux

Flux is downstream of the carrier/terrain/operator/substage chain. It is not a
root and not Axis0.

Blocked target:

```text
J_flux(engine, shell, boundary) =
  i J_i + j J_j + k J_k

J_alpha =
  R_alpha(Psi_R, engine, boundary, shell)
  - R_alpha(Psi_L, engine, boundary, shell)

alpha in {i,j,k}
```

Admission needs:

```text
finite sites
finite probes
finite boundary contraction
finite engine schedule
order swap changes J_flux
sheet erase changes J_flux
shell reversal changes j/k components
Type 1 and Type 2 schedules separate
topology freeze kills topology-mutation part
```

Not admitted as flux:

```text
right scalar - left scalar
sampled boundary gap
Axis0 sign helper
EngineCore scalar
NumPy dense-state toy
Pauli/Bloch primitive vector current
```

Current IJK receipt ceiling:

```text
non-scalar literal-quaternion IJK flux candidate on bounded explicit spinor
fixtures
not final coefficient law
not full PEPS3D environment closure
not terrain-law GKSL closure across all substages
not Axis0
not physics
```

## 19. Axis0

Axis0 is a family of downstream readouts and doctrine targets, not one closed
scalar.

Separate Axis0-near objects:

```text
terrain-square polarity:
  A0+ / N-side = {Ne, Ni}
  A0- / S-side = {Se, Si}

torus-seat diagnostic:
  rho_bar(eta) = diag(cos^2 eta, sin^2 eta)
  S(rho_bar(eta))
  b0 = sign(cos(2 eta))

cut-state bridge:
  Xi : geometry/history/flux -> rho_AB

Phi0 candidates:
  I_c(A -> B) = S(rho_B) - S(rho_AB)
  S(A|B) = S(rho_AB) - S(rho_B)
  I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)

feedback polarity:
  homeostatic compression
  allostatic reconfiguration pressure

owner genealogy:
  i-scalar
  JK fuzz
  shell bookkeeping
  universal clock
  gravity/time/dark-energy motivation
```

Axis0 zero is open:

```text
A0 ~= 0 may mean neutral, saturated, wrong cut, or branch-count artifact
```

It must not be collapsed to:

```text
i = 0
scalar entropy gap = 0
one Bloch coordinate = 0
one cut metric = final neutral truth
```

## 20. QIT-FEP

The QIT-FEP lane replaces classical hidden Markov states with finite quantum
instrument histories.

Finite instruments:

```text
I_t = {K_(t,a)}
sum_a K_(t,a)^dagger K_(t,a) = I

h = (a_1, ..., a_T)
K_h = K_(T,a_T) ... K_(1,a_1)
```

Path evidence:

```text
Z_path =
  sum_h Tr[(E_A tensor I_B)(K_h tensor I_B) rho_AB
           (K_h^dagger tensor I_B)]
```

Posterior:

```text
tau_AB =
  sum_h (sqrt(E_A) tensor I_B)
        (K_h tensor I_B) rho_AB (K_h^dagger tensor I_B)
        (sqrt(E_A) tensor I_B)

rho_AB|E = tau_AB / Tr(tau_AB)
```

Free-energy-like functional:

```text
F_Q(sigma_AB) =
  D(sigma_AB || tau_AB / Z_path) - log Z_path
```

Provisional candidate:

```text
Phi_QFEP_provisional =
  log Z_path + I_c(A -> B)_(rho_AB|E)
```

This is useful because it binds finite noncommuting histories and entangled cut
information. It is not final Axis0. The scout itself keeps `log Z_path`,
coherent information, mutual information, and aggregates separately because
component ablation does not prove one unique final scalar.

## 21. Holodeck

The Holodeck model should be preserved as a predictive reconstruction model,
not flattened into memory storage or visualization.

Core mechanism:

```text
predict
project
sense/probe
error/constraint
survivor hash or graveyard hash
update/re-enter
```

Conceptual commitments:

```text
prediction-first perception
compressed semantic traces
contextual cue field
chainable recall walks
confirmation over free recall
world-coupled identity
```

QIT-compatible finite form:

```text
finite predictive world carrier
finite cue/effect family
finite reconstruction candidate
finite error/correction instrument
finite posterior update
finite action/path comparison
```

Holodeck can later couple to QIT-FEP and Axis0:

```text
world model provides candidate histories and cues
finite effects/probes test reconstruction
graveyard/survivor hashes act as negative/positive memory constraints
Axis0-like polarity can score allostatic/homeostatic update pressure
```

But it is not:

```text
a finished runtime module
a proof of cognition
a proof of physics
a replacement for explicit graph/event state
```

## 22. Physics Boundary

Physics is a downstream interpretation target. The project can currently talk
about physics-facing ingredients:

```text
finite distinguishability
noncommuting histories
spinor/Hopf/Weyl geometry
tensor-network carriers
quaternionic flux candidates
cut-state entropy and feedback readouts
predictive world-model histories
```

But not about closed physics derivations:

```text
not Standard Model
not gravity theorem
not dark-energy theorem
not universal clock closure
not Yang-Mills/Riemann derivation
not complete attractor-basin proof
```

The physics bridge has to say:

```text
which finite object maps to which physical quantity
which invariant survives controls
which alternative is killed
which lower receipts make the map admissible
```

Without that, it is doctrine/genealogy, not a repo result.

## 23. What Current Sims Have Earned

Current bounded evidence:

```text
finite effect/SIC/Weyl substrate formal scout
finite effect algebra laws scout
8-node explicit Hopf spinor-network flux-current formal scout
8-qubit explicit-spinor entanglement engine formal scout
corrected 64-substage IGT grammar formal scout
MPS 8/16/32/64 explicit spinor scale formal scout
PEPS/PEPS3D local carrier and portability formal scouts
IJK literal-quaternion flux candidate formal scout
QIT-FEP finite noncommuting history candidate formal scout
Holodeck/science-world memory formal scouts in bounded downstream lanes
```

Current unearned claims:

```text
final manifold layer order
64 PEPS3D substage cell embedding
quaternion shell as standalone layer
final flux coefficient law
final Axis0
Xi/Phi0 closure
complete PEPS3D environment theorem
attractor-basin convergence
physics
```

## 24. How Each Object Constrains The Next

| Step | Constraint it inherits | What it adds | What it blocks if absent |
|---|---|---|---|
| finite quotient | F01/N01 | probe-relative identity | all carrier claims |
| finite effects | quotient | concrete response assignments | density/Bloch as root |
| Weyl-Heisenberg | finite effects | finite noncommuting order witness | engine order claims |
| spinor | finite carrier | phase and SU(2)/S3 structure | Hopf/Weyl/terrain claims |
| Hopf tori | spinor | fiber/base split and connection | loop placement claims |
| Weyl sheets | Hopf/spinor | L/R sign structure | chirality/terrain placement |
| PEPS3D seed | finite/spinor | site/bond/face/cell carrier | nonlocal manifold and substage cells |
| terrain generator | Weyl/Hopf | local channel/generator family | stage placement |
| operator family | finite carrier | local action/channel | substage action |
| placement | terrain + loop + sheet + token | local geometry/action context | 64-cell manifold |
| substage cell | placement + operator + PEPS3D | cell action | engine geometry |
| PEPS3D closure | substage cells | environment/contraction validity | flux/Axis0 promotion |
| flux | lower geometry | derived quaternionic current | Xi/Phi0/Axis0 bridge |
| Axis0 | flux/history/cut | feedback/cut readout | physics/Holodeck scoring |
| Holodeck/FEP | finite histories/world model | predictive reconstruction loop | cognition/physics claims |

The table is not a canon stack. It is a dependency grammar. Some objects may be
tested in partial orders or together, but no object may consume a missing lower
dependency as if it were already earned.

## 25. How To Write Future Docs Without Flattening The Model

Every future doc section should name:

```text
role:
  constraint / quotient / carrier / chart / generator / operator / schedule /
  tensor realization / current / readout / doctrine

domain:
  exact finite input object

codomain/output:
  exact finite output, invariant, or blocked readout

carrier anchor:
  PEPS3D site/bond/face/cell or explicit reason this is pre-carrier/control

spinor status:
  spinor state, spinor-derived density, or explicit control-only status

quaternion status:
  explicit map/invariant or not_applicable

order witness:
  N01 test or reason N01 is not being claimed

controls:
  label-erased, order-erased, sheet-erased, shell-erased, scalar-only, or
  carrier-erased controls as appropriate

claim ceiling:
  candidate / formal_scout / blocked / admitted
```

If a section cannot fill those fields, it can still be useful prose, but it is
not manifold evidence.
