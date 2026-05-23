# Axis 5 / Axis 6 Exploratory QIT Workout

**Created:** 2026-05-22
**Status:** exploratory workout; not canon; not source authority; no runtime promotion

## Non-Admission Rule

This packet records an exploratory Axis 5 / Axis 6 math workout.

It does not lock names, redefine axes, promote sims, or override the current
source-authority docs.

The current source-authority anchors remain:

| Axis | Current safe anchor |
|---|---|
| `Axis 5` | operator-family split: dephasing `{Ti, Te}` versus rotation `{Fi, Fe}` |
| `Axis 6` | left/right action side `A rho` versus `rho A`, represented in current token tables by up/down and operator-first/terrain-first |

Everything below is a test target or clarification surface.

## Why This Packet Exists

Recent work kept collapsing three layers:

```text
axis name
mathematical realization
derived functional role
```

This packet keeps them separate.

For Axis 6:

```text
candidate name layer:        Algebraic Action Orientation
mathematical realization:    left action A rho versus right action rho A
token-table representation:  up/down, operator-first/terrain-first
derived functional roles:    outward/inward, ascent/descent, emission/absorption, etc.
```

For Axis 5:

```text
candidate name layer:        finite-gradient algebra versus finite-spectral algebra
mathematical realization:    dephasing / dissipative family versus unitary / rotation family
token-table representation:  dephasing tokens versus rotation tokens
derived functional roles:    gradient, spectral, storage, filtering, etc.
```

The candidate names are not admitted here.

## What Was Too Shallow In The First Pass

The first pass was correctly fenced, but it did not go deep enough in four
places:

1. It did not derive the four operator maps in Bloch/PTM form.
2. It did not make Axis 6 measurable as a left/right superoperator gap.
3. It did not separate primitive one-sided actions from physical closures
   strongly enough.
4. It did not give falsifiers for the signed functional-role words
   "projector", "quantizer", "ascent", "descent", "entrainment", "damping",
   "broadcast", and "filtering".

This revision treats the pasted workout as fuel for tests, not as a name lock.

## Source Anchors To Preserve

### Axis 5

The strongest current source anchor is:

```text
Axis 5 = dephasing / projection family versus unitary / rotation family
```

At the four-operator level:

```text
dephasing family = {Ti, Te}
rotation family  = {Fi, Fe}
```

with:

```text
Ti(rho) = (1 - q1) rho + q1(P0 rho P0 + P1 rho P1)
Te(rho) = (1 - q2) rho + q2(Q+ rho Q+ + Q- rho Q-)
Fi(rho) = Ux(theta) rho Ux(theta)^dagger
Fe(rho) = Uz(phi) rho Uz(phi)^dagger
```

Any proposed name such as:

```text
Finite-Gradient Algebra
Finite-Spectral Algebra
Gradient vs Spectral
Dissipative vs Coherent
Variational vs Representation-Theoretic
```

is an exploratory naming layer unless it is row-verified against the exact
operator family split.

### Axis 6

The older formal math and operator-axis surfaces give:

```text
Axis 6 = A rho versus rho A
```

Equivalently:

```text
L_A(rho) = A rho
R_A(rho) = rho A
```

This is the left/right action or left/right module-action distinction.

The current chart/token docs represent this sign as:

```text
up   = operator-first token
down = terrain-first token
```

The audit question is not whether `A rho` and `rho A` matter. They do. The
question is whether every current token-table up/down row implements the
left/right action distinction cleanly at runtime.

## Shared Coordinate System

Use the source-native qubit density matrix:

```text
rho = [[a, u - i v],
       [u + i v, d]]

a + d = 1
a,d real
u,v real
rho >= 0
```

and the Bloch coordinate identification:

```text
rho = 1/2 (I + x sigma_x + y sigma_y + z sigma_z)

x = 2u
y = 2v
z = a - d
a = (1 + z)/2
d = (1 - z)/2
```

This gives one common arena for:

```text
operator maps
terrain maps
Axis 5 family split
Axis 6 left/right action
signed-token runtime effects
entropy/purity/readout tests
```

## Four Operator Normal Forms

This section is source-derived from the four explicit operator maps. It is not
a new canon layer.

### Ti: z-basis pinching / dephasing

Channel:

```text
Ti_q(rho) = (1 - q1) rho + q1 (P0 rho P0 + P1 rho P1)
P0 = (I + sigma_z)/2
P1 = (I - sigma_z)/2
```

Matrix action:

```text
[[a, u - i v],       [[a, (1 - q1)(u - i v)],
 [u + i v, d]]  ->    [(1 - q1)(u + i v), d]]
```

Bloch action:

```text
(x,y,z) -> ((1 - q1)x, (1 - q1)y, z)
```

Continuous generator:

```text
L_Ti(rho) = (kappa1/2)(sigma_z rho sigma_z - rho)
dx/dt = -kappa1 x
dy/dt = -kappa1 y
dz/dt = 0
```

Pauli-transfer matrix in basis `(I, X, Y, Z)`:

```text
PTM(Ti_q) =
[[1, 0,        0,        0],
 [0, 1 - q1,   0,        0],
 [0, 0,        1 - q1,   0],
 [0, 0,        0,        1]]

GEN(Ti) =
diag(0, -kappa1, -kappa1, 0)
```

Fixed algebra:

```text
Fix(Ti) = span{I, sigma_z}
```

Rigorous "gradient-like" readout:

```text
D_z(rho) = ||rho - E_z(rho)||_2^2
         = (x^2 + y^2)/2

D_z(Ti_t(rho)) = exp(-2 kappa1 t) D_z(rho)
```

So Ti is gradient-like only for the transverse-distance-to-z-fixed-algebra
functional unless another functional is explicitly named.

### Te: x-basis pinching / dephasing

Channel:

```text
Te_q(rho) = (1 - q2) rho + q2 (Q+ rho Q+ + Q- rho Q-)
Q+ = (I + sigma_x)/2
Q- = (I - sigma_x)/2
```

Matrix action:

```text
[[a, u - i v],       [[(1 - q2)a + q2/2, u - i(1 - q2)v],
 [u + i v, d]]  ->    [u + i(1 - q2)v, (1 - q2)d + q2/2]]
```

Bloch action:

```text
(x,y,z) -> (x, (1 - q2)y, (1 - q2)z)
```

Continuous generator:

```text
L_Te(rho) = (kappa2/2)(sigma_x rho sigma_x - rho)
dx/dt = 0
dy/dt = -kappa2 y
dz/dt = -kappa2 z
```

Pauli-transfer matrix:

```text
PTM(Te_q) =
[[1, 0, 0,        0],
 [0, 1, 0,        0],
 [0, 0, 1 - q2,   0],
 [0, 0, 0,        1 - q2]]

GEN(Te) =
diag(0, 0, -kappa2, -kappa2)
```

Fixed algebra:

```text
Fix(Te) = span{I, sigma_x}
```

Rigorous "gradient-like" readout:

```text
D_x(rho) = ||rho - E_x(rho)||_2^2
         = (y^2 + z^2)/2

D_x(Te_t(rho)) = exp(-2 kappa2 t) D_x(rho)
```

This is the clean version of the "Te gradient" intuition: Te descends the
distance to the sigma_x-diagonal/fixed algebra. It may ascend von Neumann
entropy, descend purity, and descend `D_x` simultaneously. The functional must
be named.

### Fi: x-axis Hamiltonian rotation

Channel:

```text
Fi_theta(rho) = U_x(theta) rho U_x(theta)^dagger
U_x(theta) = exp(-i theta sigma_x / 2)
```

Bloch action:

```text
x' = x
y' = y cos(theta) - z sin(theta)
z' = y sin(theta) + z cos(theta)
```

Continuous generator:

```text
L_Fi(rho) = -i[(omega3/2) sigma_x, rho]
dx/dt = 0
dy/dt = -omega3 z
dz/dt =  omega3 y
```

Pauli-transfer matrix:

```text
PTM(Fi_theta) =
[[1, 0, 0,           0],
 [0, 1, 0,           0],
 [0, 0, cos theta,  -sin theta],
 [0, 0, sin theta,   cos theta]]
```

Invariant readouts:

```text
spec(rho) preserved
S(rho) preserved
Tr(rho^2) preserved
||r|| preserved
```

Fi is spectral/coherent because its generator is a skew-adjoint derivation on
operator space. It cannot be called broadcast/filtering without an additional
readout or terrain context.

### Fe: z-axis Hamiltonian rotation

Channel:

```text
Fe_phi(rho) = U_z(phi) rho U_z(phi)^dagger
U_z(phi) = exp(-i phi sigma_z / 2)
```

Bloch action:

```text
x' = x cos(phi) - y sin(phi)
y' = x sin(phi) + y cos(phi)
z' = z
```

Continuous generator:

```text
L_Fe(rho) = -i[(omega4/2) sigma_z, rho]
dx/dt = -omega4 y
dy/dt =  omega4 x
dz/dt = 0
```

Pauli-transfer matrix:

```text
PTM(Fe_phi) =
[[1, 0,         0,        0],
 [0, cos phi, -sin phi,  0],
 [0, sin phi,  cos phi,  0],
 [0, 0,         0,        1]]
```

Invariant readouts:

```text
spec(rho) preserved
S(rho) preserved
Tr(rho^2) preserved
||r|| preserved
```

Fe is entrainment/damping only after coupling to a terrain or external phase
reference. Fe alone is a reversible phase rotation.

## Axis 5: Stronger Mathematical Reading

The source anchor is not merely "gradient versus spectral." It is the exact
operator-family split:

```text
Axis 5 source anchor = {Ti, Te} versus {Fi, Fe}
```

The deeper QIT reading is:

| Axis 5 side | Source operators | Channel class | Generator class | Geometry |
|---|---|---|---|---|
| dephasing / projection | `Ti`, `Te` | unital pinching semigroups | self-adjoint negative contractions on transverse subspace | contraction toward a fixed commutative subalgebra |
| rotation / unitary | `Fi`, `Fe` | inner automorphisms | skew-adjoint Hamiltonian derivations | motion on constant-spectrum orbits |

This is stronger and safer than "gradient/spectral":

```text
Ti, Te are not arbitrary Lindbladians.
They are pure dephasing conditional-expectation semigroups.

Fi, Fe are not arbitrary spectral filters.
They are Hamiltonian adjoint actions / inner automorphisms.
```

If exploratory names are used:

```text
Finite-Gradient Algebra
Finite-Spectral Algebra
```

then their admission test is:

```text
FGA must reduce to finite pinching / dephasing contractions
FSA must reduce to finite Hamiltonian adjoint rotations
```

not to vague optimization language.

## Axis 6: Stronger Mathematical Reading

Axis 6 is not an extra channel formula. It is the algebraic sidedness that is
visible before physical closure.

For `A = a . sigma` and:

```text
rho = 1/2(I + r . sigma)
```

the commutator is:

```text
[A, rho] = i (a x r) . sigma
```

Therefore the primitive left/right gap is:

```text
gap_A(rho) = ||A rho - rho A||_F
           = sqrt(2) ||a x r||
```

Consequences:

```text
gap_A(rho) = 0 iff r is parallel to a, or rho is maximally mixed.
```

Specific fixtures:

```text
gap_sigma_x(rho) = sqrt(2) sqrt(y^2 + z^2)
gap_sigma_z(rho) = sqrt(2) sqrt(x^2 + y^2)
```

This matters because these are exactly the transverse coordinates that the
source dephasing operators collapse:

```text
Te collapses y,z  <-> gap_sigma_x
Ti collapses x,y  <-> gap_sigma_z
```

So Axis 6 is not decorative. It measures the noncommuting part that the
operator can actually see.

## Liouville Matrices For Axis 6

Use column vectorization:

```text
vec([[a,b],[c,d]]) = [a,c,b,d]^T
```

Then:

```text
vec(A rho B) = (B^T otimes A) vec(rho)
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

The Hamiltonian closures are:

```text
ad_X = L_X - R_X
ad_Z = L_Z - R_Z

-i[H, rho] = -i (L_H - R_H) vec(rho)
```

The dephasing closures are:

```text
D_X = (X^* otimes X - I_4)
D_Z = (Z^* otimes Z - I_4)

L_Te = (kappa2/2) D_X
L_Ti = (kappa1/2) D_Z
```

This is the minimum mathematical substrate a sim should expose if it claims
Axis 6 is load-bearing.

## Physical-Closure Taxonomy

Primitive Axis 6 actions:

```text
rho -> A rho
rho -> rho A
```

are not generally physical channels. They must be closed.

| Closure | Formula | Physical status |
|---|---|---|
| commutator | `-i(A rho - rho A)` | Hermiticity/trace preserving generator when `A=A^dagger` |
| anti-commutator piece | `-(1/2)(M rho + rho M)` | not trace preserving alone |
| Kraus sandwich | `sum_j K_j rho K_j^dagger` | CPTP if `sum K_j^dagger K_j = I` |
| dephasing semigroup | `(kappa/2)(P rho P - rho)` for Pauli `P` | GKSL/unital CPTP semigroup |
| unitary adjoint | `U rho U^dagger` | reversible CPTP channel |

So a correct runtime row must say:

```text
axis6_primitive_side = left | right | both
closure_type = commutator | anticommutator | kraus | gksl | unitary_adjoint | other
physical_checks = trace | hermiticity | positivity | complete_positivity
```

## Signed Variants: What Is Actually Different

Source docs are explicit:

```text
UP / DOWN is not extra operator math by itself.
The operator map does not change between up and down.
```

Therefore the eight signed variants are not eight intrinsic operators. They
are:

```text
4 operator maps x 2 token/action placements
```

The signed variant can only matter through composition with a terrain map.

Let:

```text
O_j = one of {Ti, Te, Fi, Fe}
T_tau = one terrain map for tau in {Se, Ne, Ni, Si}
```

Then the sign-sensitive object must be one of:

```text
C_up   = close(O_j, T_tau, side=left/action-up)
C_down = close(O_j, T_tau, side=right/action-down)
```

or, at the token-composition layer:

```text
C_operator_first = declared_composition(O_j, T_tau)
C_terrain_first  = declared_composition(T_tau, O_j)
```

The sim must declare the convention. String order alone is not enough.

Minimal falsifier:

```text
if C_up == C_down for all states and all readouts,
then the signed variant has no runtime content for that operator-terrain row.
```

## Functional-Role Words Need Functionals

The words in the pasted workout can be useful, but only if each gets a
functional and a test.

| Word | Cannot mean | Minimal test target |
|---|---|---|
| projector | `Ti` label alone | increase/idempotence of projection onto a named fixed algebra |
| quantizer | `Ti down` label alone | reduction of admissible support against a named finite probe family |
| gradient ascent | `Te up` label alone | positive change of a named functional `F` |
| gradient descent | `Te down` label alone | negative change of the same named functional `F` |
| entrainment | `Fe up` label alone | phase-locking or reduced phase dispersion relative to a reference |
| damping | `Fe down` label alone | decay of an oscillatory mode or phase variance under terrain coupling |
| spectral broadcast | `Fi up` label alone | spreading of spectral support/readout across admitted modes |
| spectral filtering | `Fi down` label alone | contraction/selective retention of named spectral components |

No role is admitted without:

```text
operator
terrain
axis6 side / precedence
functional
before value
after value
pass/fail inequality
```

Example for Te alone:

```text
D_x = (y^2 + z^2)/2
D_x(Te_t rho) = exp(-2 kappa2 t) D_x(rho)
```

So Te is descent for `D_x`.

But for von Neumann entropy on a pure state not already fixed by `sigma_x`:

```text
S(Te_t rho) > S(rho)
```

So Te is entropy ascent in that readout.

This is why the functional role cannot be named without the functional.

## Axis 6 Math: Left And Right Regular Actions

Let:

```text
H       = finite-dimensional Hilbert space
rho     = density matrix in D(H)
A       = operator in B(H)
```

Define:

```text
L_A : rho -> A rho
R_A : rho -> rho A
```

These are linear maps on operator space `B(H)`.

They are distinct when:

```text
[A, rho] = A rho - rho A != 0
```

The commutator decomposes as:

```text
[A, rho] = L_A(rho) - R_A(rho)
```

So Axis 6 is the sidedness needed before the commutator is collapsed into one
expression.

### Liouville Representation

Using column-vectorization:

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

This gives a precise finite-dimensional test fixture for Axis 6:

```text
left_right_gap(A, rho) = ||A rho - rho A||
```

and a superoperator-level version:

```text
super_gap(A) = ||(I otimes A) - (A^T otimes I)||
```

### Important Closure Caveat

`A rho` and `rho A` are primitive operator actions, not necessarily physical
channels by themselves.

For general `A`:

```text
A rho
rho A
```

need not be Hermitian, positive, or trace-one.

So Axis 6 should be tested at two levels:

| Level | Object | Requirement |
|---|---|---|
| primitive action | `A rho` vs `rho A` | algebraic sidedness only |
| closed channel/generator | commutator, anticommutator, Kraus, Lindblad, CPTP map | physical-state preservation as applicable |

A runtime that treats `A rho` or `rho A` as a standalone density state is
wrong unless it explicitly closes or normalizes the operation and records what
closure was used.

## Axis 6 In Hamiltonian Dynamics

For a Hamiltonian `H = H^dagger`:

```text
d rho / dt = -i[H, rho]
```

This decomposes into left and right actions:

```text
-i[H, rho] = -i H rho + i rho H
```

or:

```text
-i[H, rho] = -i L_H(rho) + i R_H(rho)
```

Thus Axis 6 is visible inside the commutator:

```text
left half  = -i H rho
right half = +i rho H
```

But neither half alone is the full Hamiltonian channel.

The full physical unitary evolution is:

```text
rho(t) = U(t) rho(0) U(t)^dagger
U(t) = exp(-i H t)
```

and its infinitesimal generator includes both sides.

## Axis 6 In Lindblad / GKSL Dynamics

For a GKSL generator:

```text
L(rho) = sum_k [ L_k rho L_k^dagger
                 - 1/2 {L_k^dagger L_k, rho} ]
```

Axis 6 appears in multiple places:

```text
L_k rho L_k^dagger
```

has left action by `L_k` and right action by `L_k^dagger`.

The anticommutator decomposes as:

```text
{M, rho} = M rho + rho M
M = L_k^dagger L_k
```

so:

```text
-1/2 {M, rho} = -1/2 L_M(rho) - 1/2 R_M(rho)
```

This makes Axis 6 load-bearing in dissipative dynamics, but it does not mean
one can freely drop one side and still have a CPTP generator.

Test implication:

```text
Axis 6 probes should inspect left/right primitive terms,
then separately verify the closed generator or channel.
```

## Axis 5 Math: Current Anchor And Exploratory Renaming

### Current Source Anchor

Axis 5 is source-grounded as:

```text
dephasing family versus rotation family
```

or:

```text
{Ti, Te} versus {Fi, Fe}
```

The clean QIT names are:

| Source family | QIT class | Four-operator rows |
|---|---|---|
| dephasing / projection | pinching, dephasing, conditional expectation, unital CPTP semigroup | `Ti`, `Te` |
| rotation / unitary | inner automorphism, Hamiltonian flow, adjoint unitary action | `Fi`, `Fe` |

### Exploratory Naming Proposal

The proposed names:

```text
Finite-Gradient Algebra
Finite-Spectral Algebra
```

may be useful if they do not erase the exact source anchor.

Safer exploratory interpretation:

| Proposed name | Must reduce to | Must not imply |
|---|---|---|
| finite-gradient algebra | the `{Ti, Te}` dephasing / pinching side, plus any admitted dissipative extensions | all Lindbladians, all entropy descent, or all optimization |
| finite-spectral algebra | the `{Fi, Fe}` unitary / rotation side, plus any admitted spectral extensions | all projectors, all filtering, or all topological structure |

These names need tests before any promotion.

## Axis 5 Dephasing Side: Explicit QIT Form

The source-native dephasing generators are pure-dephasing Lindbladians:

```text
L_Ti(rho) = (kappa_1 / 2)(sigma_z rho sigma_z - rho)
L_Te(rho) = (kappa_2 / 2)(sigma_x rho sigma_x - rho)
```

They generate semigroups:

```text
Ti_t = exp(t L_Ti)
Te_t = exp(t L_Te)
```

Bloch effects:

```text
Ti: (r_x, r_y, r_z) -> (e^-kt r_x, e^-kt r_y, r_z)
Te: (r_x, r_y, r_z) -> (r_x, e^-kt r_y, e^-kt r_z)
```

These are:

```text
unital
CPTP
contractive transverse to their fixed axes
conditional expectations at t -> infinity
```

Fixed algebras:

```text
Fix(Ti) = span{I, sigma_z}
Fix(Te) = span{I, sigma_x}
```

### Entropy Correction

Do not claim:

```text
all Lindbladians increase entropy
```

That is false.

Safer statement:

```text
unital dephasing channels are entropy non-decreasing for qubits
general Lindblad dynamics can increase or decrease von Neumann entropy
```

Example:

```text
zero-temperature amplitude damping can drive a mixed state toward a pure ground state,
thereby decreasing entropy.
```

So if Axis 5 is renamed "gradient" or "dissipative", runtime rows must state
which entropy, free-energy, purity, or target-distance functional is being
measured.

## Axis 5 Rotation Side: Explicit QIT Form

The source-native rotation generators are Hamiltonian derivations:

```text
L_Fi(rho) = -i [(omega_3 / 2) sigma_x, rho]
L_Fe(rho) = -i [(omega_4 / 2) sigma_z, rho]
```

They integrate to unitary channels:

```text
Fi_theta(rho) = U_x(theta) rho U_x(theta)^dagger
Fe_phi(rho)   = U_z(phi) rho U_z(phi)^dagger
```

with:

```text
U_x(theta) = exp(-i theta sigma_x / 2)
U_z(phi)   = exp(-i phi sigma_z / 2)
```

They preserve:

```text
spec(rho)
Tr(rho^2)
S(rho)
||r||
```

They do not create attractors by themselves.

They are:

```text
reversible
entropy-preserving
Hamiltonian
orbit-generating
```

## Axis 5 x Axis 6: Test-Ready Superoperator Grid

This is a test plan, not a canon grid.

Let `A` be one of the operator generators or channel-side primitives.

| Axis 5 side | Axis 6 side | Primitive superoperator | Physical closure required |
|---|---|---|---|
| dephasing / pinching | left action | `rho -> A rho` | yes, unless embedded in full Lindblad/Kraus form |
| dephasing / pinching | right action | `rho -> rho A` | yes, unless embedded in full Lindblad/Kraus form |
| rotation / Hamiltonian | left action | `rho -> -i H rho` | yes; pair with right side for commutator |
| rotation / Hamiltonian | right action | `rho -> +i rho H` | yes; pair with left side for commutator |

Minimal validation fixture:

```text
for A in {sigma_x, sigma_z}:
  choose rho with [A, rho] != 0
  compute A rho
  compute rho A
  assert ||A rho - rho A|| > 0
  verify whether the chosen closed generator/channel preserves Hermiticity,
  positivity, and trace as claimed
```

## Axis 6 x Axis 3: Future Test Target

Axis 3 should not be collapsed into Axis 6.

Exploratory relation:

```text
Axis 3 = representation / chirality / sheet
Axis 6 = action side inside the chosen representation
```

Test target:

```text
left Weyl sheet + left action
left Weyl sheet + right action
right Weyl sheet + left action
right Weyl sheet + right action
```

Each row must keep:

```text
sheet
Hamiltonian sign
terrain law
operator family
axis6_action_side
closed channel/generator
readout
```

## Hard Fences For This Workout

Do not promote any of these without a new audit/test:

- "Algebraic Action Orientation" as a locked canonical name.
- "Finite-Gradient Algebra" or "Finite-Spectral Algebra" as locked Axis 5 names.
- "Axis 6 = not order" if the current token source uses up/down order as the representation layer.
- "Axis 5 = all Lindblad" or "Axis 5 = all gradient descent".
- "Spectral class = all projectors or all filtering".
- A one-sided action `A rho` or `rho A` as a physical density state without closure.
- Entropy monotonicity for arbitrary Lindblad dynamics.
- Axis 3 / chirality and Axis 6 / action-side equivalence.

## Work Items If This Thread Continues

1. Build an Axis 6 primitive-action probe:

```text
L_A(rho)=A rho
R_A(rho)=rho A
Liouville matrices I otimes A and A^T otimes I
left/right gap on Pauli fixtures
```

2. Build an Axis 5 source-anchor probe:

```text
Ti/Te dephasing channels:
  fixed algebras
  PTM spectra
  entropy/purity behavior

Fi/Fe unitary channels:
  spectrum preservation
  PTM rotations
  entropy invariance
```

3. Build an Axis 5 x Axis 6 cross probe:

```text
left/right primitive pieces of Hamiltonian commutator
left/right primitive pieces of Lindblad anticommutator
closed-generator checks
```

4. Only after those pass, test candidate names:

```text
Algebraic Action Orientation
Finite-Gradient Algebra
Finite-Spectral Algebra
```

against source rows and runtime rows.

## Bottom Line

This workout is useful as an exploration plan.

It is not canon.

The safe current state remains:

```text
Axis 5 = dephasing {Ti, Te} versus rotation {Fi, Fe}
Axis 6 = left action A rho versus right action rho A,
         represented in current token tables as up/down precedence
```
