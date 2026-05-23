# Axes / Terrains / Operators / Constraint-Manifold Source Layout

**Created:** 2026-05-22
**Status:** source-grounded synthesis and row-matrix audit; no runtime promotion

## Purpose

This packet lays out the current source-backed structure of:

```text
geometric constraint manifold
axes 0-6
four terrain/topology families
eight terrain/path realizations
four judging operators
sixteen ordered tokens
two engine type charts
open flux placement
```

It also checks a live hypothesis:

```text
A3 x A4 x A5 x A6 = 16 ordered tokens
```

Result:

```text
false as stated.
```

The source-backed token identity is:

```text
A1 x A2 x A5 x A6 = 16 ordered tokens
```

while:

```text
A3 x A4 x A5 x A6 = 8 paired loop-placement signatures
```

`A3` and `A4` are not useless. They place the tokens into fiber/base loop
geometry and deductive/inductive loop-order families. They do not, by
themselves, distinguish all 16 tokens.

## Source Anchors

Primary source slices read:

```text
READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md
READ ONLY Reference Docs/JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP copy.md
READ ONLY Reference Docs/Weyl Flux.md
```

Key line anchors:

| Source object | Lines |
|---|---|
| full manifold ladder | AXES atlas lines 73-96 |
| global axis table | AXES atlas lines 173-181 |
| A3 exact path split | AXES atlas lines 345-361 |
| A4 loop-order family | AXES atlas lines 380-419 |
| A5 operator-family split | AXES atlas lines 423-470 |
| A6 precedence/token law | AXES atlas lines 474-515 |
| eight terrain table | AXES atlas lines 569-580 |
| signed judging variants | AXES atlas lines 584-595 |
| engine type charts | AXES atlas lines 610-626; JUNGIAN map lines 304-330 |
| flux status | Weyl Flux lines 4-84 |

## Constraint-Manifold Ladder

The current source ladder is:

| Order | Layer | Exact object | Role |
|---|---|---|---|
| 1 | root constraints | `F01_FINITUDE`, `N01_NONCOMMUTATION` | admissibility roots |
| 2 | admissibility set | `C` | finite rule/probe set |
| 3 | admissible manifold | `M(C)` | allowed configuration domain |
| 4 | axis-slice rule | `A_i : M(C) -> V_i` | axes read out slices of `M(C)` |
| 5 | finite QIT carrier | `H = C^2`, `D(C^2)`, Pauli basis | minimal live state space |
| 6 | spinor carrier | `S^3 = {psi in C^2 : ||psi||=1}` | normalized spinor geometry |
| 7 | Hopf projection | `pi(psi)=psi^dagger sigma psi in S^2` | spinor-to-Bloch map |
| 8 | Bloch image | `S^2` | pure-state density image |
| 9 | torus stratum | `T_eta subset S^3` | nested Hopf-torus seat |
| 10 | Clifford torus | `T_(pi/4)` | symmetric torus seat |
| 11 | fiber loop | `gamma_fiber^s(u)` | density-stationary path |
| 12 | lifted-base loop | `gamma_base^s(u)` | density-traversing path |
| 13 | left Weyl sheet | `psi_left in S^3` | left sheet |
| 14 | right Weyl sheet | `psi_right in S^3` | right sheet |
| 15 | left density | `rho_left=psi_left psi_left^dagger` | left density |
| 16 | right density | `rho_right=psi_right psi_right^dagger` | right density |
| 17 | engine runtime manifold | paired sheet state + torus coordinates + stage controls | live engine state |
| 18 | bridge target | `Xi : geometry/history -> rho_AB` | open |
| 19 | cut-state family | `rho_AB`, `rho_A`, `rho_B` | open |
| 20 | Axis 0 kernel | `Phi_0(rho_AB)` | open but narrowed |

This is the correct scale: the manifold is not downstream decoration. It is the
admissible ratchet surface on which the axes, terrains, operators, and engine
placements are read.

## Carrier And Geometry

Finite density state:

```text
rho = 1/2(I + r_x sigma_x + r_y sigma_y + r_z sigma_z)
```

Base Hamiltonian:

```text
H_0 = n_x sigma_x + n_y sigma_y + n_z sigma_z
```

Spinor chart:

```text
psi_s(phi, chi; eta)
= [ exp(i(phi + chi)) cos eta,
    exp(i(phi - chi)) sin eta ]^T

s in {left,right}
eta in [0, pi/2]
phi, chi in [0, 2pi)
```

Hopf map:

```text
pi(psi)=psi^dagger (sigma_x, sigma_y, sigma_z) psi
```

Density reduction:

```text
rho(psi)=|psi><psi|=1/2(I+r.sigma)
```

Hopf connection:

```text
A = -i psi^dagger d psi = d phi + cos(2 eta) d chi
```

Loop laws:

```text
fiber:
  gamma_fiber^s(u)=psi_s(phi_0+u, chi_0; eta_0)
  rho_fiber^s(u)=rho_fiber^s(0)

lifted base:
  gamma_base^s(u)=psi_s(phi_0-cos(2 eta_0)u, chi_0+u; eta_0)
  A(dot gamma_base^s)=0
  rho_base^s(u)=|gamma_base^s(u)><gamma_base^s(u)|
```

Weyl sheets:

```text
H_left  = +H_0
H_right = -H_0
rho_left  = psi_left psi_left^dagger
rho_right = psi_right psi_right^dagger
```

## Axes 0-6

### Axis 0

Current role:

```text
entropy drive and later cut-state functional
```

Current seats:

```text
torus latitude / torus seat
later Phi_0(rho_AB)
```

Open bridge:

```text
Xi : geometry/history -> rho_AB
Phi_0(rho_AB) likely from coherent/conditional/mutual information family
```

Axis 0 is not one of the six structural token lines. It drives through them.

### Axis 1

Current source role:

```text
derived terrain branch split
```

Current exact split:

```text
{Se, Ni} versus {Ne, Si}
```

In topology identification, `A1` is one of the two bits needed to distinguish
the four terrain/topology families.

### Axis 2

Current source role:

```text
direct versus conjugated frame
```

Current exact split:

```text
direct:      {Se, Ne}
conjugated:  {Si, Ni}
```

with:

```text
tilde(rho)=rho
tilde(rho)=V_s^dagger rho V_s
```

`A1 x A2` identifies the four topology families:

| Topology | A1 branch | A2 frame |
|---|---|---|
| `Se` | `Se/Ni` side | direct |
| `Ni` | `Se/Ni` side | conjugated |
| `Ne` | `Ne/Si` side | direct |
| `Si` | `Ne/Si` side | conjugated |

### Axis 3

Current source-backed primitive:

```text
fiber loop versus lifted-base loop
```

Not:

```text
chirality
flux
loose outer/inner without path qualification
```

Exact split:

| A3 side | Path | Density behavior |
|---|---|---|
| fiber | `gamma_fiber^s(u)=psi_s(phi_0+u,chi_0;eta_0)` | `rho_fiber^s(u)=rho_fiber^s(0)` |
| lifted base | `gamma_base^s(u)=psi_s(phi_0-cos(2eta_0)u,chi_0+u;eta_0)` | `rho_base^s(u)` changes |

Chart correlation:

```text
inner token set versus outer token set
```

But inner/outer is engine-chart placement. It is not the deepest geometry,
because fiber is inner in engine type one and outer in engine type two.

### Axis 4

Current source-backed primitive:

```text
loop-order family
```

Exact families:

```text
deductive:
  Phi_deductive = U o E o U o E

inductive:
  Phi_inductive = E o U o E o U
```

Current runtime correlation:

| A4 family | Token-family label |
|---|---|
| deductive | `FeTi` family |
| inductive | `TeFi` family |

The pair-language `TiFe` versus `FeTi` is a recorded correlation/proposal
layer, not the exact active math anchor.

### Axis 5

Current source-backed primitive:

```text
operator family
```

Exact split:

| A5 side | Operators | QIT class |
|---|---|---|
| dephasing/projection | `Ti`, `Te` | unital pinching / pure dephasing channels |
| rotation/unitary | `Fi`, `Fe` | Hamiltonian unitary adjoint channels |

This is the safe anchor. Exploratory words like gradient/spectral must reduce
to these exact operator maps.

### Axis 6

Current source token law:

```text
up   = operator written first
down = terrain written first
```

Current derivation relation:

```text
b_6 = - b_0 b_3
```

Exact token split:

| A6 side | Meaning | Token family |
|---|---|---|
| up | judging/operator first | `TiSe`, `TiNe`, `FeSi`, `FeNi`, `TeNi`, `TeSi`, `FiNe`, `FiSe` |
| down | perceiving/terrain first | `SeTi`, `NeTi`, `SiFe`, `NiFe`, `NiTe`, `SiTe`, `NeFi`, `SeFi` |

QIT audit requirement:

```text
axis6_action_side = left action A rho | right action rho A
```

The token law and QIT left/right action are related but not automatically the
same. Runtime rows must declare both:

```text
token_precedence
axis6_action_side
closure_type
```

## Four Operator Maps

The four judging operators are maps on density matrices, not terrain classes.

| Operator | Exact channel | Generator | Family | Native frame |
|---|---|---|---|---|
| `Ti` | `(1-q1)rho + q1(P0 rho P0 + P1 rho P1)` | `(k1/2)(sigma_z rho sigma_z - rho)` | dephasing/projection along z | direct `Se/Ne` |
| `Te` | `(1-q2)rho + q2(Q+ rho Q+ + Q- rho Q-)` | `(k2/2)(sigma_x rho sigma_x - rho)` | dephasing/projection along x | conjugated `Ni/Si` |
| `Fi` | `U_x(theta) rho U_x(theta)^dagger` | `-i[(omega3/2)sigma_x,rho]` | unitary rotation about x | direct `Se/Ne` |
| `Fe` | `U_z(phi) rho U_z(phi)^dagger` | `-i[(omega4/2)sigma_z,rho]` | unitary rotation about z | conjugated `Ni/Si` |

Bloch effects:

```text
Ti: (x,y,z) -> ((1-q1)x, (1-q1)y, z)
Te: (x,y,z) -> (x, (1-q2)y, (1-q2)z)
Fi: rotation in the y-z plane about x
Fe: rotation in the x-y plane about z
```

Important:

```text
UP/DOWN does not change these operator formulas.
```

UP/DOWN changes ordered-token placement and any terrain-composite readout.

## Four Terrain / Topology Families

The perceiving functions are topology/terrain laws. They are not the judging
operator maps.

| Terrain | Expansion/compression | Open/closed | Frame | Native operators | Dynamical reading |
|---|---|---|---|---|---|
| `Se` | expansion | open/isothermal | direct | `Ti`, `Fi` | dissipative release plus weak coherent term |
| `Ne` | expansion | closed/adiabatic | direct | `Ti`, `Fi` | Hamiltonian circulation plus weak dissipator |
| `Ni` | compression | open/isothermal | conjugated | `Te`, `Fe` | attractor Lindblad / sink-source compression |
| `Si` | compression | closed/adiabatic | conjugated | `Te`, `Fe` | projector/dephasing around a commuting basis |

These four terrain laws are then embedded in two path classes:

| Runtime terrain | Topology | A3 path | Density law | Frame | Native operators | Engine realization |
|---|---|---|---|---|---|---|
| `Se_f` | `Se` | fiber | density stationary | direct | `Ti`, `Fi` | T1 inner, T2 outer |
| `Si_f` | `Si` | fiber | density stationary | conjugated | `Te`, `Fe` | T1 inner, T2 outer |
| `Ne_f` | `Ne` | fiber | density stationary | direct | `Ti`, `Fi` | T1 inner, T2 outer |
| `Ni_f` | `Ni` | fiber | density stationary | conjugated | `Te`, `Fe` | T1 inner, T2 outer |
| `Se_b` | `Se` | lifted base | density traversing | direct | `Ti`, `Fi` | T1 outer, T2 inner |
| `Si_b` | `Si` | lifted base | density traversing | conjugated | `Te`, `Fe` | T1 outer, T2 inner |
| `Ne_b` | `Ne` | lifted base | density traversing | direct | `Ti`, `Fi` | T1 outer, T2 inner |
| `Ni_b` | `Ni` | lifted base | density traversing | conjugated | `Te`, `Fe` | T1 outer, T2 inner |

## Sixteen Ordered Tokens

The exact token law is:

```text
topology x operator family x precedence
```

| Topology | dephasing up | dephasing down | rotation up | rotation down |
|---|---|---|---|---|
| `Se` | `TiSe` | `SeTi` | `FiSe` | `SeFi` |
| `Ne` | `TiNe` | `NeTi` | `FiNe` | `NeFi` |
| `Ni` | `TeNi` | `NiTe` | `FeNi` | `NiFe` |
| `Si` | `TeSi` | `SiTe` | `FeSi` | `SiFe` |

Source implication:

```text
16 token identity = A1 x A2 x A5 x A6
```

because:

```text
A1 x A2 -> one of {Se, Ne, Ni, Si}
A5      -> dephasing or rotation
A6      -> up/operator-first or down/terrain-first
```

## Engine Charts

### Engine Type One

Engine type one uses:

```text
outer loop: deductive order on lifted base
inner loop: inductive order on fiber
```

| Step | Topology | Outer token | Outer loop | Inner token | Inner loop |
|---|---|---|---|---|---|
| 1 | `Se` | `TiSe` | lifted-base/deductive | `SeFi` | fiber/inductive |
| 2 | `Ne` | `NeTi` | lifted-base/deductive | `FiNe` | fiber/inductive |
| 3 | `Ni` | `NiFe` | lifted-base/deductive | `TeNi` | fiber/inductive |
| 4 | `Si` | `FeSi` | lifted-base/deductive | `SiTe` | fiber/inductive |

### Engine Type Two

Engine type two uses:

```text
outer loop: inductive order on fiber
inner loop: deductive order on lifted base
```

| Step | Topology | Outer token | Outer loop | Inner token | Inner loop |
|---|---|---|---|---|---|
| 1 | `Se` | `FiSe` | fiber/inductive | `SeTi` | lifted-base/deductive |
| 2 | `Si` | `TeSi` | fiber/inductive | `SiFe` | lifted-base/deductive |
| 3 | `Ni` | `NiTe` | fiber/inductive | `FeNi` | lifted-base/deductive |
| 4 | `Ne` | `NeFi` | fiber/inductive | `TiNe` | lifted-base/deductive |

## Full Row Matrix

Columns:

```text
token
engine type
topology
A1 branch
A2 frame
A3 path
chart loop
A4 loop order
operator
A5 family
A6 precedence
```

### Engine Type One Rows

| Token | Engine | Topology | A1 | A2 | A3 path | Loop | A4 | Operator | A5 | A6 |
|---|---|---|---|---|---|---|---|---|---|---|
| `TiSe` | T1 | `Se` | Se/Ni | direct | base | outer | deductive | `Ti` | dephasing | up |
| `NeTi` | T1 | `Ne` | Ne/Si | direct | base | outer | deductive | `Ti` | dephasing | down |
| `NiFe` | T1 | `Ni` | Se/Ni | conjugated | base | outer | deductive | `Fe` | rotation | down |
| `FeSi` | T1 | `Si` | Ne/Si | conjugated | base | outer | deductive | `Fe` | rotation | up |
| `SeFi` | T1 | `Se` | Se/Ni | direct | fiber | inner | inductive | `Fi` | rotation | down |
| `FiNe` | T1 | `Ne` | Ne/Si | direct | fiber | inner | inductive | `Fi` | rotation | up |
| `TeNi` | T1 | `Ni` | Se/Ni | conjugated | fiber | inner | inductive | `Te` | dephasing | up |
| `SiTe` | T1 | `Si` | Ne/Si | conjugated | fiber | inner | inductive | `Te` | dephasing | down |

### Engine Type Two Rows

| Token | Engine | Topology | A1 | A2 | A3 path | Loop | A4 | Operator | A5 | A6 |
|---|---|---|---|---|---|---|---|---|---|---|
| `FiSe` | T2 | `Se` | Se/Ni | direct | fiber | outer | inductive | `Fi` | rotation | up |
| `TeSi` | T2 | `Si` | Ne/Si | conjugated | fiber | outer | inductive | `Te` | dephasing | up |
| `NiTe` | T2 | `Ni` | Se/Ni | conjugated | fiber | outer | inductive | `Te` | dephasing | down |
| `NeFi` | T2 | `Ne` | Ne/Si | direct | fiber | outer | inductive | `Fi` | rotation | down |
| `SeTi` | T2 | `Se` | Se/Ni | direct | base | inner | deductive | `Ti` | dephasing | down |
| `SiFe` | T2 | `Si` | Ne/Si | conjugated | base | inner | deductive | `Fe` | rotation | down |
| `FeNi` | T2 | `Ni` | Se/Ni | conjugated | base | inner | deductive | `Fe` | rotation | up |
| `TiNe` | T2 | `Ne` | Ne/Si | direct | base | inner | deductive | `Ti` | dephasing | up |

## Projection Audit

### Projection 1: `A1 x A2 x A5 x A6`

This projection uniquely identifies all 16 tokens.

Reason:

```text
A1 x A2 identifies topology
A5 identifies operator family
A6 identifies precedence
```

### Projection 2: `A3 x A4 x A5 x A6`

This projection does not uniquely identify all 16 tokens.

It gives 8 paired signatures:

| A3 | A4 | A5 | A6 | Tokens |
|---|---|---|---|---|
| base | deductive | dephasing | up | `TiSe`, `TiNe` |
| base | deductive | dephasing | down | `NeTi`, `SeTi` |
| base | deductive | rotation | up | `FeSi`, `FeNi` |
| base | deductive | rotation | down | `NiFe`, `SiFe` |
| fiber | inductive | dephasing | up | `TeNi`, `TeSi` |
| fiber | inductive | dephasing | down | `SiTe`, `NiTe` |
| fiber | inductive | rotation | up | `FiNe`, `FiSe` |
| fiber | inductive | rotation | down | `SeFi`, `NeFi` |

Therefore:

```text
A3 x A4 x A5 x A6 = paired loop-placement signatures, not token identity.
```

This is the main correction to the pasted Claude hypothesis.

### Projection 3: Engine Type

Engine type is not recovered by `A3 x A4` alone.

For source rows:

```text
T1:
  outer = base + deductive
  inner = fiber + inductive

T2:
  outer = fiber + inductive
  inner = base + deductive
```

So the same `(A3,A4)` pairs appear in both engine types:

```text
base + deductive appears in T1 outer and T2 inner
fiber + inductive appears in T1 inner and T2 outer
```

Engine type requires at least:

```text
chart loop placement + path/order pairing
```

and probably also:

```text
sheet / H sign / chirality bookkeeping
```

Flux may later explain the difference, but it is not admitted yet.

## Flux Placement

Flux source status:

```text
open derived object
candidate family
not primitive
not yet placed below axes, inside an axis, or across axes
```

Candidate family:

```text
J_geom  = geometric transport
J_chi   = chirality separation
J_Bloch = differential Bloch current
J_ent   = entropic asymmetry
J_cut   = cut-state information current
J_axis  = axis-internal readout
J_cross = coupled multi-axis observable
```

Decision gates:

```text
does flux survive before rho_AB?
does it survive on geometry variables alone?
does no-chirality collapse it?
does loop-swap or fiber/base flattening kill it?
does one axis explain it?
does it require multi-axis coupling?
```

Current safe wording:

```text
flux is a derived candidate family over stagewise changes and manifold
transport, not a current axis and not a new root constraint.
```

## Clean Current Architecture

```text
F01 + N01
  -> C
  -> M(C)
  -> H=C^2 and D(C^2)
  -> S3 spinor carrier
  -> Hopf projection S3 -> S2
  -> Hopf tori T_eta
  -> fiber/base loop laws
  -> left/right Weyl sheets
  -> terrain laws Se/Ne/Ni/Si
  -> operator maps Ti/Te/Fi/Fe
  -> ordered tokens from topology x operator-family x precedence
  -> engine charts from path-class x loop-order arrangements
  -> open flux candidate family
  -> open Xi bridge to rho_AB
  -> open Phi_0 cut-state kernel
```

## Claims This Layout Supports

| Claim | Status |
|---|---|
| geometric constraint manifold is the ratchet surface | source-backed framing |
| four operators are clear and explicit | source-backed |
| four terrain families are not operator maps | source-backed |
| each terrain has fiber/base realization | source-backed |
| 16 tokens are topology x operator family x precedence | source-backed |
| A3 is fiber/base, not flux | source-backed |
| A4 is loop-order family, not just pair label | source-backed |
| A5 is dephasing/rotation family | source-backed |
| A6 source token law is up/down precedence | source-backed |
| A6 QIT realization needs left/right action audit | strong audit requirement |
| A3-A6 generate 16 tokens | falsified as stated |
| flux is pre-axial root | not admitted |
| engine type = A3 x A4 | not proven; probably underdetermined |

## Next Work

The next real work is a small source-native matrix/probe pair:

1. Write a machine-readable `16_token_axis_projection_matrix.json`.
2. Add checks:

```text
unique(A1,A2,A5,A6) == 16
unique(A3,A4,A5,A6) == 8
engine_type_recoverable_from(A3,A4) == false
engine_type_recoverable_from(chart_loop,A3,A4) == true or needs sheet/sign
```

3. Only after that, test flux candidates against engine type:

```text
canonical T1/T2
one-stage flux flip
all-stage flux flip
sheet sign flip
token table flip
loop swap
fiber/base flattening
```

That is the path from source layout to a real engine/manifold falsifier.
