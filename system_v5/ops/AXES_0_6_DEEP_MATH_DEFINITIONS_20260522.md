# Axes 0-6 Deep Math Definitions

Status: source-grounded axis workout with explicit math, runtime readouts, and
falsifiers. This file does not promote exploratory names to canon. It deepens
the axis layer so the axes are maps over the constraint manifold, not labels.

Primary source anchors:

- `system_v5/READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md`
- `system_v5/READ ONLY Reference Docs/JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP copy.md`
- `system_v5/READ ONLY Reference Docs/operator math explicit.md`
- `system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md`
- `system_v5/ops/TERRAIN_GENERATOR_SOURCE_LAYOUT_20260522.md`
- `system_v5/ops/QIT_ENGINE_FULL_EXPLICIT_MATH_PACKET_20260522.md`

## 0. Purpose

The shallow failure mode is:

```text
Axis = a label or a Jungian word.
```

The corrected math form is:

```text
Axis = a finite readout/projection A_i : M(C) -> V_i
       with a concrete domain, codomain, invariant, runtime witness,
       and falsifier.
```

This file defines the axes in that second form.

The important separation is:

```text
terrain math  = generator vector fields / GKSL laws
operator math = channel and superoperator maps
token math    = ordered grammar over topology, operator family, and precedence
axis math     = projections/readouts over M(C)
engine math   = charted composition of terrain placements and operator tokens
```

Do not collapse these layers.

## 1. Shared Domain And Notation

Root constraints:

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

Local QIT realization:

```text
H = C^2
D(H) = { rho in B(H) : rho >= 0, Tr(rho) = 1 }

rho = 1/2 (I + r_x sigma_x + r_y sigma_y + r_z sigma_z)
r = (r_x, r_y, r_z), ||r|| <= 1

H_0 = n_x sigma_x + n_y sigma_y + n_z sigma_z
H_L = +H_0
H_R = -H_0
```

Carrier:

```text
psi_s(phi, chi; eta)
  = [ exp(i(phi + chi)) cos eta,
      exp(i(phi - chi)) sin eta ]^T

s in {L, R}
eta in [0, pi/2]
phi, chi in [0, 2 pi)

pi(psi) = psi^dagger (sigma_x, sigma_y, sigma_z) psi in S^2

r(phi, chi; eta)
  = (sin(2 eta) cos(2 chi),
     -sin(2 eta) sin(2 chi),
     cos(2 eta))

A_Hopf = -i psi^dagger d psi = d phi + cos(2 eta) d chi
```

The negative `r_y` sign follows from the stated spinor chart and the standard
Pauli `sigma_y` convention. At `(phi, chi, eta) = (0, pi/4, pi/4)`, the density
has `tr(rho sigma_y) = -1`; the plus-sign transcription is rejected by the
working-math audit.

Runtime point:

```text
x in M(C)
x contains at least:
  rho_s or psi_s
  sheet s in {L, R}
  torus coordinates (eta, phi, chi)
  path class
  terrain generator X_{tau,s}
  judging operator O in {Ti, Te, Fi, Fe}
  loop chart role
  ordered token
  finite probe readouts

when the bridge exists:
  Xi(history, geometry) -> rho_AB
  Phi_0(rho_AB)
```

Each axis should be recorded with:

```text
axis_source_value:
  value named by the source docs

axis_math_object:
  concrete formula being evaluated

axis_runtime_witness:
  finite probe or state transition that distinguishes the sides

axis_falsifier:
  finite condition under which the row has no load-bearing content
```

## 2. Axis 0: Entropy Polarity / Cut-State Kernel

### 2.1 Domain

Axis 0 has two current seats:

```text
chart seat:
  torus latitude eta and its induced one-qubit density chart

bridge seat:
  later cut state rho_AB from Xi : geometry/history -> rho_AB
```

The chart seat exists now. The final bridge seat is still open.

### 2.2 Chart Math

The current chart density is:

```text
rho_bar(eta) = diag(cos^2 eta, sin^2 eta)
```

Let:

```text
p(eta) = cos^2 eta
1 - p(eta) = sin^2 eta
```

Von Neumann entropy:

```text
S_eta
  = - cos^2 eta log(cos^2 eta)
    - sin^2 eta log(sin^2 eta)
```

Derivative:

```text
dS_eta/d eta
  = - sin(2 eta) log(tan^2 eta)
```

For `0 < eta < pi/2`, this derivative changes sign at:

```text
eta = pi/4
```

The source chart polarity is:

```text
b_0 = sign(cos(2 eta)) = sign(r_z)
```

So:

```text
eta < pi/4  -> b_0 = +1
eta = pi/4  -> b_0 = 0 threshold / Clifford torus
eta > pi/4  -> b_0 = -1
```

This is a one-dimensional polarity readout of the entropy landscape on the
torus chart. It is not yet the final `Phi_0(rho_AB)`.

### 2.3 Cut-State Candidates

When the bridge exists:

```text
Xi : geometry/history -> rho_AB
rho_A = Tr_B(rho_AB)
rho_B = Tr_A(rho_AB)
```

Candidate signed kernels include:

```text
I_c(A -> B)_rho = S(rho_B) - S(rho_AB)

S(A|B)_rho = S(rho_AB) - S(rho_B)

I(A:B)_rho = S(rho_A) + S(rho_B) - S(rho_AB)

Phi_shell(rho_AB)
  = sum_r w_r I_c(A_r -> B_r)
```

The atlas currently narrows the final seat toward coherent-information or
conditional-entropy style cut kernels, but the bridge is not closed.

### 2.4 What Axis 0 Distinguishes

Axis 0 distinguishes which side of the entropy-polarity threshold a state or
cut-state occupies.

At the chart layer it is:

```text
A_0_chart(eta) = sign(cos(2 eta))
```

At the bridge layer it must become:

```text
A_0_bridge(history, geometry)
  = sign(Phi_0(Xi(history, geometry)))
```

### 2.5 What Axis 0 Cannot Do Alone

Axis 0 alone does not identify:

```text
terrain topology
operator family
path class
loop order
left/right action
engine type
flux
```

It drives and constrains lower axes, but does not replace them.

### 2.6 Runtime Witness

Minimal witness:

```text
sample eta values on both sides of pi/4
compute S_eta
compute dS_eta/d eta
compute b_0 = sign(cos(2 eta))
```

Bridge witness, when available:

```text
construct rho_AB from Xi
compute I_c, S(A|B), I(A:B)
show which candidate separates the intended control families
```

### 2.7 Falsifier

Axis 0 bridge claim fails if:

```text
Phi_0 is claimed but Xi is absent
```

or:

```text
candidate Phi_0 cannot separate the claimed control families
under finite admissible probes.
```

Chart Axis 0 and bridge Axis 0 must not be silently identified.

## 3. Axis 1: Derived Terrain Branch

### 3.1 Domain

Axis 1 acts on terrain/topology family identification. It is not a standalone
operator and not a channel.

Source split:

```text
A_1 branch = {Se, Ni} versus {Ne, Si}
```

This axis is derived in the lower stack rather than primitive. It is still
load-bearing because it supplies one of the two topology bits.

### 3.2 Codomain

Use a branch bit:

```text
A_1 = 0 : Se/Ni side
A_1 = 1 : Ne/Si side
```

The sign convention can be changed, but the partition cannot be changed without
changing the source mapping.

### 3.3 Topology Identification With Axis 2

Axis 1 alone does not identify a terrain. Axis 1 plus Axis 2 does:

```text
A_1 x A_2 -> {Se, Ne, Ni, Si}
```

Current matrix:

```text
A_1 = open/isothermal branch,   A_2 = expansion/direct       -> Se
A_1 = closed/adiabatic branch,  A_2 = expansion/direct       -> Ne
A_1 = open/isothermal branch,   A_2 = compression/conjugated -> Ni
A_1 = closed/adiabatic branch,  A_2 = compression/conjugated -> Si
```

This is the load-bearing use of Axis 1 in token identity:

```text
A_1 x A_2 x A_5 x A_6 = 16 ordered tokens
```

### 3.3.1 Source-Correct Derivation From Axis 0 And Axis 2

Axis 1 is derived from Axis 0 and Axis 2, but the derivation is not the same
as the `A_1 x A_2` lookup above.

Terminology note:

```text
The atlas sometimes says "upper" and "lower" Bloch hemispheres.
Those are coordinate aliases only:

A_0+ / N-side = eta < pi/4 = r_z > 0
A_0- / S-side = eta > pi/4 = r_z < 0

They are not model-native terrain names and they are not Axis 6 up/down.
Use A_0+ and A_0- in new packets unless quoting the source.
```

Source Axis 0 color/topology sets:

```text
A_0+ / N-side / white = {Ne, Ni}
A_0- / S-side / black = {Se, Si}
```

This does make structural sense as Axis 0: it is the diagonal/parity split
through the terrain square, not another local terrain property.

Native terrain square:

| | A_2 expansion / direct | A_2 compression / conjugated |
|---|---|---|
| A_1 open / isothermal | `Se` = A_0- | `Ni` = A_0+ |
| A_1 closed / adiabatic | `Ne` = A_0+ | `Si` = A_0- |

So:

```text
A_0+ = {Ne, Ni}
A_0- = {Se, Si}
```

Axis 0 is therefore the cross-cutting polarity that chooses which branch of
the `A_1 x A_2` square is active. It is not the same kind of axis as Axis 1 or
Axis 2.

Source Axis 2 frame/topology sets:

```text
A_2 expansion / direct       = {Se, Ne}
A_2 compression / conjugated = {Ni, Si}
```

Therefore the source-correct intersection table is:

```text
A_0+ / N-side, A_2 expansion/direct        -> Ne -> A_1 closed/adiabatic
A_0+ / N-side, A_2 compression/conjugated  -> Ni -> A_1 open/isothermal
A_0- / S-side, A_2 expansion/direct        -> Se -> A_1 open/isothermal
A_0- / S-side, A_2 compression/conjugated  -> Si -> A_1 closed/adiabatic
```

This table is the correction to a common failure mode:

```text
wrong:
  A_0+ + direct -> Se
  A_0- + direct -> Ne

source-correct:
  A_0+ + direct -> Ne
  A_0- + direct -> Se
```

So `A_1` can be used with `A_2` to identify a topology, but when deriving
`A_1` from `A_0` and `A_2`, use the set-intersection table above.

### 3.4 What Axis 1 Distinguishes

It distinguishes the branch that pairs:

```text
Se with Ni
Ne with Si
```

This can be read as a terrain-branch partition, not as a complete terrain law.
The actual terrain law still lives in the eight sheet-specific generators.

### 3.5 What Axis 1 Cannot Do Alone

Axis 1 cannot distinguish:

```text
Se from Ni
Ne from Si
direct frame from conjugated frame
sheet L from sheet R
fiber from lifted base
token up from token down
```

### 3.6 Runtime Witness

For every token row, record:

```text
topology_label
A_1_branch
A_2_frame
```

and verify:

```text
(A_1_branch, A_2_frame) maps to topology_label.
```

### 3.7 Falsifier

A claimed Axis 1 implementation fails if:

```text
A_1 is used to identify a terrain without A_2.
```

It also fails if any row maps:

```text
direct + Se/Ni side -> not Se
direct + Ne/Si side -> not Ne
conjugated + Se/Ni side -> not Ni
conjugated + Ne/Si side -> not Si
```

without an explicit source-level convention change.

## 4. Axis 2: Direct Versus Conjugated Frame

### 4.1 Domain

Axis 2 is a representation-frame axis for the state and generator.

Source split:

```text
direct:      {Se, Ne}
conjugated:  {Ni, Si}
```

### 4.2 Direct Frame

Direct frame means:

```text
tilde(rho) = rho
dot(rho) = L(rho)
```

The generator is read in the lab/current frame.

### 4.3 Conjugated Frame

Let:

```text
V_s(u) = exp(-i H_s u)
H_L = +H_0
H_R = -H_0
```

Define:

```text
tilde(rho) = V_s(u)^dagger rho V_s(u)
```

Then:

```text
dot(tilde rho)
  = V_s^dagger L(V_s tilde rho V_s^dagger) V_s
    - i[-K, tilde rho]

K = i V_s^dagger dot(V_s)
```

Equivalent sign conventions for the gauge term must be declared by the sim.
The load-bearing point is that the conjugated frame contains the transport
correction; it is not the same equation as direct-frame evolution.

### 4.4 What Axis 2 Distinguishes

Axis 2 distinguishes whether the terrain law is read directly or after
co-moving sheet transport.

In topology identification:

```text
A_2 = direct      -> Se or Ne, depending on A_1
A_2 = conjugated  -> Ni or Si, depending on A_1
```

### 4.5 What Axis 2 Cannot Do Alone

Axis 2 alone cannot distinguish:

```text
Se from Ne
Ni from Si
operator family
loop path
loop order
token precedence
```

It is also not identical to chirality. The sheet sign `H_L=+H_0`,
`H_R=-H_0` enters the frame transport, but Axis 2 is the representation-frame
choice, not the whole sheet/flux story.

### 4.6 Runtime Witness

For direct rows:

```text
check tilde(rho) == rho
check generator used as L(rho)
```

For conjugated rows:

```text
compute V_s
compute tilde(rho) = V_s^dagger rho V_s
include gauge/transport term in dot(tilde rho)
```

### 4.7 Falsifier

Axis 2 is not implemented if:

```text
direct and conjugated rows use the same generator in the same frame
```

or if:

```text
conjugated rows omit the V_s transport/gauge correction.
```

## 5. Axis 3: Fiber Versus Lifted-Base Path

### 5.1 Domain

Axis 3 is a path-class axis on the Hopf carrier.

It is not:

```text
chirality
flux
loose inner/outer
```

The source primitive is:

```text
fiber loop versus lifted-base loop
```

### 5.2 Fiber Path

Fiber path:

```text
gamma_fiber^s(u)
  = psi_s(phi_0 + u, chi_0; eta_0)
```

Density:

```text
rho_fiber^s(u)
  = |gamma_fiber^s(u)><gamma_fiber^s(u)|
  = rho_fiber^s(0)
```

The state moves in spinor phase while the density matrix is stationary.

Vector field:

```text
Y_in psi_s = partial_phi psi_s
```

### 5.3 Lifted-Base Path

Lifted-base path:

```text
gamma_base^s(u)
  = psi_s(phi_0 - cos(2 eta_0) u,
          chi_0 + u;
          eta_0)
```

Horizontal condition:

```text
A_Hopf(dot(gamma_base^s)) = 0
```

Density:

```text
rho_base^s(u)
  = |gamma_base^s(u)><gamma_base^s(u)|
```

This density changes with `u`.

Vector field:

```text
Y_out psi_s = (-cos(2 eta) partial_phi + partial_chi) psi_s
```

### 5.4 What Axis 3 Distinguishes

Axis 3 distinguishes:

```text
density-stationary Hopf fiber motion
versus
density-traversing horizontal lifted-base motion
```

This is stronger than saying inner/outer.

### 5.5 Chart Correlation

The chart role swaps by engine:

```text
Engine type 1:
  outer = lifted base + deductive
  inner = fiber + inductive

Engine type 2:
  outer = fiber + inductive
  inner = lifted base + deductive
```

Therefore:

```text
outer/inner is chart-relative
fiber/base is the source math anchor
```

### 5.6 Relation To Axis 6

Axis 6 is derived in the source lower stack as:

```text
b_6 = - b_0 b_3
```

The `b_3` used in this XOR table is the chart-role bit:

```text
b_3 = +1 for outer
b_3 = -1 for inner
```

It is not the raw geometric path bit. The raw path must still be recorded as
fiber versus lifted base, because that is the manifold witness. Type 2 swaps
the chart role of the paths, so using raw fiber/base inside the XOR inverts
every Type-2 row.

So Axis 3 has two non-interchangeable readouts:

```text
geometry readout: fiber versus lifted base
XOR readout:      inner versus outer chart role
```

Axis 3 participates in the precedence law through the chart-role readout. That
does not make Axis 3 itself precedence.

### 5.7 Runtime Witness

Fiber witness:

```text
||rho_fiber(u) - rho_fiber(0)|| = 0
```

Lifted-base witness:

```text
||rho_base(u) - rho_base(0)|| > 0
for generic u and eta not at degenerate points
```

Horizontal witness:

```text
A_Hopf(dot(gamma_base)) = 0
```

Holonomy/closure witness:

```text
horizontal integral of the connection is zero by construction,
but Berry closure phase appears in psi_end versus psi_0.
```

### 5.8 Falsifier

Axis 3 is collapsed if a sim only compares final density matrices and misses
the path or spinor closure phase.

It also fails if:

```text
fiber path changes density generically
```

or:

```text
lifted-base path is not horizontal under A_Hopf.
```

## 6. Axis 4: Loop-Order Family

### 6.1 Domain

Axis 4 is a loop-order family over unitary and non-unitary branches.

It is not a single judging operator, and it is not the same as Axis 6
precedence.

### 6.2 Exact Source Families

The source writes:

```text
deductive:
  Phi_deductive = U circle E circle U circle E

inductive:
  Phi_inductive = E circle U circle E circle U
```

where:

```text
U = unitary branch
E = non-unitary or dissipative branch
```

Every implementation must declare composition convention. In standard
mathematical notation:

```text
(A circle B)(rho) = A(B(rho))
```

so the rightmost map acts first. If a sim uses left-to-right execution logs, it
must record both the log order and the mathematical composition order.

### 6.3 Runtime Correlation

The current runtime correlation is:

```text
deductive loop family -> FeTi family
inductive loop family -> TeFi family
```

The atlas also records older/proposal pair language. That layer should not
override the explicit runtime loop-order formulas.

### 6.4 What Axis 4 Distinguishes

Axis 4 distinguishes order-sensitive channel composition:

```text
Phi_deductive != Phi_inductive
```

when noncommutation makes order observable.

Define the finite witness:

```text
Delta_4(rho)
  = Phi_deductive(rho) - Phi_inductive(rho)
```

Probe norm:

```text
||Delta_4||_P
  = max_{rho in finite probe set P} ||Delta_4(rho)||_F
```

### 6.5 What Axis 4 Cannot Do Alone

Axis 4 cannot identify:

```text
topology
operator family
path class
token precedence
engine type
```

It also cannot replace Axis 6. Axis 4 is order family across a loop. Axis 6 is
token precedence plus primitive action-side audit.

### 6.6 Runtime Witness

For each engine loop:

```text
record U maps
record E maps
record mathematical composition
compute Phi_deductive or Phi_inductive
evaluate Delta_4 against the opposite family on finite probes
```

### 6.7 Falsifier

Axis 4 is not load-bearing for a row if:

```text
Phi_deductive(rho) = Phi_inductive(rho)
for all admissible finite probes.
```

For example, complete dephasing can erase order effects. That was the failure
mode in earlier tests where the state collapsed to `I/2` in one step.

## 7. Axis 5: Operator Family / Dephasing Versus Rotation

### 7.1 Domain

Axis 5 acts on the judging-operator family:

```text
{Ti, Te} versus {Fi, Fe}
```

Safe source anchor:

```text
dephasing/projection family versus rotation/unitary family
```

Exploratory names like finite-gradient algebra and finite-spectral algebra are
allowed only as explanatory overlays if they reduce exactly to these maps.

### 7.2 Dephasing / Projection Side

Ti:

```text
Ti_q(rho)
  = (1 - q_1) rho
    + q_1 (P_0 rho P_0 + P_1 rho P_1)

P_0 = 1/2(I + sigma_z)
P_1 = 1/2(I - sigma_z)

L_Ti(rho)
  = (kappa_1/2)(sigma_z rho sigma_z - rho)
```

Bloch action:

```text
(x, y, z) -> ((1 - q_1)x, (1 - q_1)y, z)
dot x = -kappa_1 x
dot y = -kappa_1 y
dot z = 0
```

Fixed algebra:

```text
Fix(Ti) = span{I, sigma_z}
```

Distance to fixed algebra:

```text
D_z(rho) = ||rho - E_z(rho)||_F^2 = (x^2 + y^2)/2
D_z(Ti_t rho) = exp(-2 kappa_1 t) D_z(rho)
```

Te:

```text
Te_q(rho)
  = (1 - q_2) rho
    + q_2 (Q_+ rho Q_+ + Q_- rho Q_-)

Q_+ = 1/2(I + sigma_x)
Q_- = 1/2(I - sigma_x)

L_Te(rho)
  = (kappa_2/2)(sigma_x rho sigma_x - rho)
```

Bloch action:

```text
(x, y, z) -> (x, (1 - q_2)y, (1 - q_2)z)
dot x = 0
dot y = -kappa_2 y
dot z = -kappa_2 z
```

Fixed algebra:

```text
Fix(Te) = span{I, sigma_x}
```

Distance to fixed algebra:

```text
D_x(rho) = ||rho - E_x(rho)||_F^2 = (y^2 + z^2)/2
D_x(Te_t rho) = exp(-2 kappa_2 t) D_x(rho)
```

These are unital pinching/dephasing semigroups. They are entropy
non-decreasing for qubits, but they are not a license to say all Lindbladians
increase entropy.

### 7.3 Rotation / Unitary Side

Fi:

```text
Fi_theta(rho) = U_x(theta) rho U_x(theta)^dagger
U_x(theta) = exp(-i theta sigma_x/2)

L_Fi(rho) = -i[(omega_3/2) sigma_x, rho]
```

Bloch action:

```text
x' = x
y' = y cos theta - z sin theta
z' = y sin theta + z cos theta
```

Fe:

```text
Fe_phi(rho) = U_z(phi) rho U_z(phi)^dagger
U_z(phi) = exp(-i phi sigma_z/2)

L_Fe(rho) = -i[(omega_4/2) sigma_z, rho]
```

Bloch action:

```text
x' = x cos phi - y sin phi
y' = x sin phi + y cos phi
z' = z
```

Invariants for Fi and Fe:

```text
spec(rho)
S(rho)
Tr(rho^2)
||r||
```

### 7.4 Axis 5 Math Class Reading

The dephasing side is:

```text
finite pinching
conditional expectation onto a commutative fixed algebra
self-adjoint negative contraction on transverse Bloch components
CPTP semigroup
```

The rotation side is:

```text
Hamiltonian inner automorphism
skew-adjoint commutator derivation
constant-spectrum SU(2) orbit motion
reversible CPTP group action
```

This is the precise content behind any gradient/spectral language.

### 7.5 What Axis 5 Distinguishes

Axis 5 distinguishes:

```text
contractive projection/dephasing dynamics
versus
unitary spectral rotation dynamics
```

It does not distinguish Ti from Te or Fi from Fe by itself. It only selects
the family. Topology and native frame help choose the specific operator row.

### 7.6 Runtime Witness

Dephasing witness:

```text
fixed algebra distance D_x or D_z contracts
transverse Bloch components decay
PTM has eigenvalues with magnitude < 1 on transverse components
```

Rotation witness:

```text
||r|| preserved
spec(rho) preserved
PTM is an orthogonal rotation block
```

### 7.7 Falsifier

Axis 5 is overclaimed if:

```text
"gradient" is used to mean every Lindblad generator
```

or:

```text
"spectral" is used to mean every projector/decomposition.
```

It is collapsed in a runtime row if the alleged dephasing and rotation
operators have identical action on every finite probe readout.

## 8. Axis 6: Token Precedence And Left/Right Action Audit

### 8.1 Source Token Law

Source token split:

```text
up   = operator written first
down = terrain written first
```

Full token law:

```text
Se: TiSe / SeTi / FiSe / SeFi
Ne: TiNe / NeTi / FiNe / NeFi
Ni: TeNi / NiTe / FeNi / NiFe
Si: TeSi / SiTe / FeSi / SiFe
```

Derived lower-stack relation:

```text
b_6 = - b_0 b_3
```

Here `b_3` is the inner/outer chart-role bit:

```text
outer -> b_3 = +1
inner -> b_3 = -1
```

It is not the raw fiber/base geometry bit. The source chart makes this
observable: Type 1 has outer = lifted base and inner = fiber, while Type 2 has
outer = fiber and inner = lifted base. Therefore a receipt must record both:

```text
A3_geometry_path = fiber | lifted_base
A3_chart_role    = inner | outer
```

So Axis 6 is not an independent free symbolic bit in the current lower stack.
It is still a real runtime distinction because the token order and primitive
action-side can be audited.

### 8.2 QIT Action-Side Realization

For an operator `A`:

```text
L_A(rho) = A rho
R_A(rho) = rho A
```

Commutator:

```text
[A, rho] = L_A(rho) - R_A(rho)
```

Column-vector convention:

```text
vec(A rho B) = (B^T tensor A) vec(rho)
L_A ~ I tensor A
R_A ~ A^T tensor I
```

For Pauli `A = a . sigma` and:

```text
rho = 1/2(I + r . sigma)
```

the commutator is:

```text
[A, rho] = i (a x r) . sigma
```

and the finite noncommutation gap is:

```text
gap_A(rho)
  = ||A rho - rho A||_F
  = sqrt(2) ||a x r||
```

Specific fixtures:

```text
gap_{sigma_x}(rho) = sqrt(2) sqrt(y^2 + z^2)
gap_{sigma_z}(rho) = sqrt(2) sqrt(x^2 + y^2)
```

These are exactly the transverse components collapsed by Te and Ti,
respectively.

### 8.3 Physical Closure

`A rho` and `rho A` are primitive side actions. They are not generally
standalone physical channels.

Physical closures include:

```text
Hamiltonian commutator:
  -i(A rho - rho A)

anti-commutator dissipative piece:
  -1/2(M rho + rho M)

Kraus sandwich:
  sum_j K_j rho K_j^dagger
  CPTP iff sum_j K_j^dagger K_j = I

unitary adjoint:
  U rho U^dagger

dephasing semigroup:
  (kappa/2)(P rho P - rho), Pauli P
```

Therefore a runtime row must not claim a left or right primitive action is a
CPTP channel unless the closure is specified.

### 8.4 Two-Layer Requirement

Every runtime row that claims Axis 6 must record both:

```text
axis6_token_precedence:
  up | down

axis6_action_side:
  left | right | both | closure-only
```

These are related but not automatically identical.

Example:

```text
token = TiSe
axis6_token_precedence = up
operator channel = Ti_q
physical implementation may still use both sides inside sigma_z rho sigma_z
or commutator/anti-commutator closure.
```

So the token grammar and QIT action-side audit must both be present.

### 8.5 What Axis 6 Distinguishes

Axis 6 distinguishes:

```text
ordered token grammar
and
algebraic side of primitive action under noncommutation
```

The token layer distinguishes `TiSe` from `SeTi`. The QIT layer measures
whether left and right actions are actually different for the state being
processed.

### 8.6 What Axis 6 Cannot Do Alone

Axis 6 is not:

```text
time
causality
strategy priority
loop order
operator family
terrain topology
chirality
flux
```

Those may be derived readings only after the primitive math is recorded.

### 8.7 Runtime Witness

For primitive action:

```text
compute gap_A(rho) = ||A rho - rho A||_F
```

For token order:

```text
compare token-up composed stage and token-down composed stage
with terrain and operator fixed.
```

For physical closure:

```text
record closure_type
check trace preservation
check positivity or Choi positivity when CPTP is claimed
```

### 8.8 Falsifier

Axis 6 has no runtime content in a row if:

```text
gap_A(rho) = 0
```

and:

```text
C_up(rho) = C_down(rho)
for every finite admissible probe rho and readout.
```

It is also invalid if a sim claims:

```text
A rho
```

or:

```text
rho A
```

as a complete physical channel without closure.

## 9. Inter-Axis Projection Structure

### 9.1 Token Identity

The corrected token identity is:

```text
16 ordered tokens = A_1 x A_2 x A_5 x A_6
```

because:

```text
A_1 x A_2 -> one topology in {Se, Ne, Ni, Si}
A_5       -> dephasing or rotation
A_6       -> up or down token order
```

So:

```text
4 topologies x 2 operator families x 2 precedence values = 16 tokens
```

This is not optional. It corrects the earlier wrong projection:

```text
A_3 x A_4 x A_5 x A_6 != 16 token identity
```

### 9.2 Loop-Placement Signatures

The projection:

```text
A_3 x A_4 x A_5 x A_6
```

gives paired loop-placement signatures. It does not uniquely identify all 16
tokens.

Source result:

```text
A_3 x A_4 x A_5 x A_6 = 8 paired signatures
```

because the same path/order/family/precedence signature can pair two topology
rows.

### 9.3 Engine Type

Engine type is not recovered from `A_3 x A_4` alone.

Source chart:

```text
T1:
  outer = lifted base + deductive
  inner = fiber + inductive

T2:
  outer = fiber + inductive
  inner = lifted base + deductive
```

The same `(A_3, A_4)` pairs occur in both engine types. Engine type requires
the chart placement vector, and likely sheet/H-sign bookkeeping:

```text
engine type needs:
  chart loop role
  path/order pairing
  sheet sign H_L or H_R
  token row
```

Flux may later explain or compress part of this distinction, but flux is not
yet admitted as a replacement for the chart vector.

### 9.4 Terrain Placements Are A Different 16

There are also:

```text
16 terrain placements
  = 4 terrain families x 2 Weyl sheets x 2 path classes
```

Form:

```text
(X_{tau,s}, Gamma_ell^s)
tau in {Se, Ne, Ni, Si}
s in {L, R}
ell in {fiber, lifted-base}
```

These are generator/path objects, not ordered token identities.

The two 16-counts are:

```text
16 ordered tokens:
  grammar over topology, operator family, precedence

16 terrain placements:
  dynamical generator on sheet and path
```

They must be joined by an engine chart. They are not the same layer.

## 10. Axis Runtime Receipt Schema

Every stage-level receipt should include:

```json
{
  "stage_id": "...",
  "engine_type": "T1 or T2",
  "sheet": "L or R",
  "terrain_family": "Se|Ne|Ni|Si",
  "terrain_law": "Funnel|Cannon|Vortex|Spiral|Pit|Source|Hill|Citadel",
  "path_class": "fiber|lifted_base",
  "chart_loop_role": "inner|outer",
  "loop_order_family": "deductive|inductive",
  "token": "TiSe etc",
  "operator": "Ti|Te|Fi|Fe",
  "axis_values": {
    "A0": {"seat": "chart|bridge", "value": "...", "witness": "..."},
    "A1": {"branch": "SeNi|NeSi"},
    "A2": {"frame": "direct|conjugated"},
    "A3": {
      "geometry_path": "fiber|lifted_base",
      "chart_role": "inner|outer",
      "xor_bit_source": "chart_role"
    },
    "A4": {"loop_order": "deductive|inductive"},
    "A5": {"operator_family": "dephasing|rotation"},
    "A6": {
      "token_precedence": "up|down",
      "action_side": "left|right|both|closure_only",
      "closure_type": "commutator|kraus|unitary_adjoint|dephasing|..."
    }
  },
  "finite_witnesses": {
    "A0_entropy": "...",
    "A2_frame_transport": "...",
    "A3_path_density": "...",
    "A4_order_gap": "...",
    "A5_family_invariant": "...",
    "A6_noncommutation_gap": "..."
  },
  "falsifiers": {
    "A0_bridge_absent": false,
    "A3_path_collapsed": false,
    "A4_order_collapsed": false,
    "A5_family_collapsed": false,
    "A6_side_collapsed": false
  }
}
```

This receipt shape prevents a row from saying "Axis 6 down" or "Axis 5
gradient" without showing the actual math.

## 11. Minimal Test Battery

Axis 0:

```text
sample eta below and above pi/4
verify sign(cos(2 eta))
verify dS/deta changes sign at pi/4
```

Axis 1 x Axis 2:

```text
enumerate four topology rows
verify matrix maps to Se, Ne, Ni, Si
```

Axis 2:

```text
direct row uses L(rho)
conjugated row uses V^dagger L(V rho V^dagger) V plus gauge term
```

Axis 3:

```text
fiber density stationary
lifted-base density traversing
lifted-base horizontal condition holds
```

Axis 4:

```text
compare U o E o U o E with E o U o E o U
on finite probe states
avoid complete-dephasing one-step collapse
```

Axis 5:

```text
Ti/Te contract fixed-algebra distance
Fi/Fe preserve spectrum and Bloch norm
```

Axis 6:

```text
compute ||A rho - rho A||_F
compare up/down composed stages
record closure type and CPTP checks
```

Projection:

```text
enumerate A1 x A2 x A5 x A6 -> 16 tokens
enumerate A3 x A4 x A5 x A6 -> 8 paired signatures
enumerate 16 terrain placements separately
```

## 12. Flux Boundary

Flux is not promoted in this axis file.

The safe current state is:

```text
flux candidates have simulation/readout evidence in prior runs
canonical flux identity and placement are still open
```

Candidate families include:

```text
J_geom
J_chi
J_Bloch
J_ent
J_cut
J_axis
J_cross
```

Flux may become a manifold-level derived observable, an axis-internal readout,
or a cross-axis observable. It must not be used to replace Axis 3, Axis 4, or
the engine chart until an admission test proves that replacement.

## 13. Bottom Line

The deep axis stack is:

```text
A0: entropy polarity / cut-state kernel
A1: derived branch bit used with A2 to identify topology
A2: direct versus conjugated representation frame
A3: fiber versus lifted-base path class
A4: deductive versus inductive loop-order family
A5: dephasing/pinching versus rotation/unitary operator family
A6: token precedence plus left/right primitive action audit
```

The corrected projections are:

```text
A1 x A2                     -> terrain/topology family
A1 x A2 x A5 x A6            -> 16 ordered tokens
A3 x A4 x A5 x A6            -> 8 paired loop-placement signatures
terrain x sheet x path       -> 16 terrain placements
engine chart                 -> joins token grammar to terrain placements
```

Any future sim or doc that collapses these projections should be treated as a
failed axis implementation until it is corrected.
