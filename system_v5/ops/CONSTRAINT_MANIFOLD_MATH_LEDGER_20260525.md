# Constraint Manifold Math Ledger

**Created:** 2026-05-25
**Status:** quarantined draft; not a source-backed layer order and not a promotion receipt

## 2026-05-25 Quarantine Notice

Do not use this file as an admitted manifold layer order. A follow-up audit
found that this draft mixes different object types:

- root constraints and quotient/admission rules;
- carriers and coordinate charts;
- Hopf-torus geometry and loop fields;
- optional representation tools such as quaternions;
- runtime engine stage/token/substage inventory;
- PEPS3D carrier realization;
- downstream flux, Xi, Phi0, and Axis0 readouts.

Those are not all the same kind of "layer." In particular:

- `quaternion shell geometry` is not admitted here as a separate manifold layer;
  it is only usable after an explicit map/invariant/test shows what it adds
  beyond the spinor/Hopf structure.
- `PEPS3D` is not a late layer proved after substages; it is the finite
  spinor-network carrier that must be active from the first admitted finite
  carrier/probe step in nonclassical manifold work. Every later object must
  say how it is carried on finite PEPS3D sites, bonds, faces, or cells.
- The current 64-substage scout proves at most a stage/token inventory
  scaffold. It does not prove 64 substages as manifold cells.
- Flux and Axis0 remain blocked while `foundation_closed=false`,
  `flux_layer_allowed=false`, and `downstream_axis0_allowed=false`.

Use `system_v5/ops/TUI_MANIFOLD_LAYER_FAILURE_AUDIT_20260525.md` for the
current repair boundary.

This ledger records blocked candidate targets and repair constraints. It does
not pin a final layer order. The only pinned rule is fail-closed admission from
F01/N01 through explicit finite, torch-native, spinor/quaternion, PEPS3D-carried
maps before any downstream flux, Axis0, PEPS3D closure, or physics claim.

Current gate state:

```text
foundation_closed = false
peps3d_from_start_required = true
substage_cell_embedding_proven = false
quaternion_layer_admitted = false
flux_queue_allowed = false
axis0_queue_allowed = false
physics_claim_allowed = false
```

The immediate correction is:

```text
flux is a blocked derived candidate family over the constraint manifold
Axis0 is a downstream signed entropy/FEP readout
```

So flux must not be implemented as a late scalar gap around Axis0. It must be
derived only after the lower finite maps, carrier anchors, controls, and
substage cells are source-conformant, and before the Xi/Phi0/Axis0 cut-state
readout.

## 1. Root Constraint Manifold

The root object is not a vector space, Bloch sphere, Pauli axis system, or
Cartesian coordinate chart. The root object is finite distinguishability under
noncommuting admissible operations.

Finite states and probes:

```text
S = finite admissible state/configuration set
P = finite admissible probe/effect family

s1 ~_P s2  iff  for all p in P: p(s1) = p(s2)

Q_P = S / ~_P
```

Root constraints:

```text
F01_FINITUDE:
  |S| < infinity
  |P| < infinity
  dim(H) < infinity
  finite operator registry
  finite path/history registry

N01_NONCOMMUTATION:
  A o B != B o A in general
  A rho != rho A in general
  ~_(A o B) != ~_(B o A) in general
```

Admissibility set and manifold:

```text
C = {
  F01_FINITUDE,
  N01_NONCOMMUTATION,
  finite probe/effect rules,
  finite composition rules,
  no primitive identity/equality/time/metric/probability/optimization
}

M(C) = { x in S : x satisfies C }

A_i : M(C) -> V_i
```

The axes are readout maps from the admissible manifold. They are not primitive
substances.

## 2. Admission Chain, Not Layer Order

There is no admitted final layer stack in this file. Do not promote any list of
names as source-backed manifold order. A candidate step is admitted only when it
defines all of:

```text
domain D_i
finite PEPS3D carrier slice K_i
map f_i : D_i -> D_(i+1) or invariant I_i(D_i)
output object O_i on K_i
F01 witness: finite sites/probes/operators/paths
N01 witness: order-sensitive or noncommuting control
negative/control condition
blocked downstream consumers
```

For nonclassical manifold work, PEPS3D is part of the carrier from the first
finite carrier admission. It is not appended after engine/substage labels:

```text
F01 + N01
  -> C
  -> M(C)
  -> finite probe/effect quotient Q_P
  -> finite PEPS3D spinor-network carrier K_0 with probe/effect indices
```

All later candidates are constraints, charts, maps, or readouts on that finite
carrier. They remain candidate stack/nesting surfaces until sims prove their
domains, maps, controls, and composition order:

```text
local spinor sections psi_v in S^3 on K
nested Hopf tori T_eta(v) as spinor submanifolds/charts on K
quaternionic orientation map q_v in H_1 only if a map/invariant is proven
left/right Weyl sheet cover on the same PEPS3D-carried spinor shell
terrain generator plus loop-field placements
operator-substage cells with local state/action evidence
flux candidate as derived quaternionic chiral boundary current
Xi/Phi0/Axis0 as downstream readouts after flux admission
```

The prior failure mode was working on:

```text
PEPS3D-ish scalar row -> flux gap -> Axis0 sign
```

before proving:

```text
finite probe substrate
PEPS3D-carried local spinor sections
nested Hopf tori on the spinor carrier
quaternionic orientation map/invariant if quaternions are used
terrain generator plus loop-field placements
engine token/substage cell embedding
```

That is downstream work on an unbuilt object.

## 3. Local Spinor Carrier

Local spinor chart:

```text
psi_s(phi, chi; eta)
 =
 [ exp(i(phi + chi)) cos eta,
   exp(i(phi - chi)) sin eta ]^T

s in {L, R}
eta in [0, pi/2]
phi, chi in [0, 2pi)
||psi_s|| = 1
```

Density is an admitted carrier/readout, not the root:

```text
rho_s = psi_s psi_s^dagger
```

Hopf connection:

```text
A_Hopf = -i psi_s^dagger d psi_s
       = d phi + cos(2 eta) d chi
```

Fiber loop:

```text
gamma_f^s(u) = psi_s(phi_0 + u, chi_0; eta_0)
rho_f^s(u) = rho_f^s(0)
```

Lifted-base loop:

```text
gamma_b^s(u) =
  psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)

A_Hopf(dot gamma_b^s) = 0
rho_b^s(u) changes with u
```

Left/right sheet Hamiltonians:

```text
H_L = +H_0
H_R = -H_0

rho_dot_L = -i[H_L, rho_L]
rho_dot_R = -i[H_R, rho_R]
```

Pauli/Bloch formulas can appear only as admitted finite carrier charts or
adapter controls. They are not root geometry.

Nested Hopf torus carrier requirement:

```text
E_eta = finite shell index set
eta_k in [0, pi/2] for k in E_eta

T_eta(k,v) = {
  psi_v(phi, chi; eta_k) :
  phi, chi in finite admitted phase grid or bounded symbolic chart
}

shell_projection:
  pi_shell(v,k,phi,chi) = (v,k)

nesting/order candidate:
  N_shell(k1,k2) = admitted relation between T_eta(k1) and T_eta(k2)
```

Required controls before Weyl, terrain, stage, substage, or flux language can
use the torus stack:

```text
finite-shell control: E_eta erased or collapsed
Hopf-control: A_Hopf omitted or replaced by flat phase labels
order-control: shell order reversed where an order-sensitive claim is made
PEPS3D-control: no finite site/cell anchor
```

If `T_eta`, finite shell indices, Hopf connection, and controls are not present,
the work is not on nested Hopf tori; it is using Hopf words as labels.

## 4. Quaternion/Spinor Shell Representation, Not Standalone Layer

The shell object must not be modeled as Cartesian xyz. The aligned shell object
must be a finite map or invariant on PEPS3D-carried spinor/Hopf data. A
quaternion is not admitted by naming `i`, `j`, and `k`; it is admitted only if
the sim defines what the quaternion map changes, preserves, or forbids.

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

Shell orientation variable:

```text
q_shell(v,k) = a + b i + c j + d k
||q_shell(v,k)|| = 1
```

For the user's current model frame:

```text
i, j, k = shell-time / temporal-orientation components
j/k = shell fuzz and past/future boundary orientation candidates
```

Minimum admissible quaternion use:

```text
carrier anchor:
  (v,k) = finite PEPS3D site/cell v and finite shell index k

domain:
  psi_v in S^3
  T_eta(k,v) = nested Hopf torus chart through psi_v

map or invariant:
  q_shell : (v,k,psi_v,T_eta) -> H_1
  or
  I_q(v,k) = invariant that changes under admitted shell reversal/order swap

N01 witness:
  q-bound action after terrain/operator action != before-action control

negative controls:
  q erased
  q commuted/order-erased
  q replaced by Cartesian xyz labels
```

The formal target is not a Euclidean vector current. It is a finite
quaternionic spinor-shell transport object carried by PEPS3D cells. If that
map/invariant is missing, quaternion language is label-only and must not count
as a layer.

## 5. Terrain Generators

Terrain is the generator. Loop is the spinor path field. Placement is
generator plus loop.

Terrain symbols are Rosetta labels unless the sim supplies an explicit domain
and operator family:

```text
domain:
  finite PEPS3D-carried spinor/density cells
  nested Hopf torus index k
  sheet s in {L,R}

generator:
  X_(tau,s,k) : rho_(v,s,k) -> rho_dot_(v,s,k)

carrier:
  torch complex tensors, admitted finite operator basis, finite PEPS3D anchor

controls:
  Cartesian/Bloch primitive interpretation blocked
  label-only Se/Ne/Ni/Si interpretation blocked
  commuting/order-erased control included when a noncommuting claim is made
```

Counts:

```text
terrain families = 4
  {Se, Ne, Ni, Si}

terrains = 8
  {(Se,L),(Se,R),(Ne,L),(Ne,R),(Ni,L),(Ni,R),(Si,L),(Si,R)}

loop placements = 16
  {(tau, s, ell) :
     tau in {Se,Ne,Ni,Si},
     s in {L,R},
     ell in {fiber, base}}
```

Dissipator:

```text
D[L](rho) = L rho L^dagger - 1/2(L^dagger L rho + rho L^dagger L)
```

Type 1 / left terrain laws:

```text
Se / Funnel:
  X_F^L(rho_L) =
    sum_k D[L_k^(F,L)](rho_L) - i eps_(F,L)[H_L, rho_L]

Ne / Vortex:
  X_V^L(rho_L) =
    -i[H_L, rho_L] + eps_(V,L) sum_k D[M_k^(V,L)](rho_L)

Ni / Pit:
  X_P^L(rho_L) =
    gamma_(P,L) D[sigma_-](rho_L) - i eps_(P,L)[H_L, rho_L]

Si / Hill:
  X_H^L(rho_L) =
    -i[K_L, rho_L]
    + sum_j kappa_(H,L,j)(
        P_j^(H,L) rho_L P_j^(H,L)
        - 1/2(P_j^(H,L) rho_L + rho_L P_j^(H,L))
      )
```

Type 2 / right terrain laws:

```text
Se / Cannon:
  X_C^R(rho_R) =
    sum_k D[L_k^(C,R)](rho_R) - i eps_(C,R)[H_R, rho_R]

Ne / Spiral:
  X_S^R(rho_R) =
    -i[H_R, rho_R] + eps_(S,R) sum_k D[M_k^(S,R)](rho_R)

Ni / Source:
  X_So^R(rho_R) =
    gamma_(So,R) D[sigma_+](rho_R) - i eps_(So,R)[H_R, rho_R]

Si / Citadel:
  X_Ci^R(rho_R) =
    -i[K_R, rho_R]
    + sum_j kappa_(Ci,R,j)(
        P_j^(Ci,R) rho_R P_j^(Ci,R)
        - 1/2(P_j^(Ci,R) rho_R + rho_R P_j^(Ci,R))
      )
```

## 6. Engine Type Tables

Type 1 has left-sheet terrain realization and the following charted tokens:

| Topology | Outer token | Outer operator | Outer A6 | Inner token | Inner operator | Inner A6 |
|---|---|---|---|---|---|---|
| Se | TiSe | Ti | up | SeFi | Fi | down |
| Ne | NeTi | Ti | down | FiNe | Fi | up |
| Ni | NiFe | Fe | down | TeNi | Te | up |
| Si | FeSi | Fe | up | SiTe | Te | down |

Type 2 has right-sheet terrain realization and different token placements:

| Topology | Outer token | Outer operator | Outer A6 | Inner token | Inner operator | Inner A6 |
|---|---|---|---|---|---|---|
| Se | FiSe | Fi | up | SeTi | Ti | down |
| Ne | NeFi | Fi | down | TiNe | Ti | up |
| Ni | NiTe | Te | down | FeNi | Fe | up |
| Si | TeSi | Te | up | SiFe | Fe | down |

These tables are the source-level difference between engine type 1 and engine
type 2. The same four topology families appear, but the sheet, loop placement,
operator, token order, and A6 sign are changed.

## 7. Axes 0-6 Math

Axis 0, current torus seat:

```text
rho_bar(eta) =
  (1 / 2pi) int_0^(2pi) rho(chi, eta) d chi
  = diag(cos^2 eta, sin^2 eta)

S(rho_bar(eta)) =
  -cos^2 eta log(cos^2 eta)
  -sin^2 eta log(sin^2 eta)

b0 = sign(cos(2 eta))
```

Axis 0, downstream open cut-state readout target:

```text
Xi : geometry/history/flux -> rho_AB

Phi0 candidates:
  I_c(A -> B) = S(rho_B) - S(rho_AB)
  S(A|B)     = S(rho_AB) - S(rho_B)
  I(A:B)     = S(rho_A) + S(rho_B) - S(rho_AB)
```

Axis 1:

```text
A1 = derived branch split
{Se, Ni} versus {Ne, Si}
```

Axis 2:

```text
direct frame:
  rho_tilde = rho
  rho_dot = L(rho)

conjugated frame:
  rho_tilde = V^dagger rho V
  rho_tilde_dot =
    V^dagger L(V rho_tilde V^dagger) V - i[-K, rho_tilde]
  K = i V^dagger V_dot
```

Axis 3:

```text
fiber path       = density-stationary
lifted-base path = density-traversing and Hopf-horizontal
```

Axis 4:

```text
Phi_deductive = U o E o U o E
Phi_inductive = E o U o E o U
```

Axis 5:

```text
dephasing family = {Ti, Te}
rotation family  = {Fi, Fe}
```

Axis 6:

```text
b6 = -b0 b3

up   = operator-first token
down = terrain-first token

L_A(rho) = A rho
R_A(rho) = rho A
[A, rho] = L_A(rho) - R_A(rho)
```

## 8. PEPS3D Carrier From First Admitted Finite Carrier

The PEPS3D object must be a spinor network whose contraction carrier is a
3D tensor network. It is not "a dense vector with a PEPS label."

For nonclassical manifold work, the PEPS3D carrier begins when the finite
probe/effect carrier is admitted:

```text
K = (V, E, F, C)

V = finite sites
E = finite bonds
F = finite faces/boundary patches
C = finite cells or substage-cell anchors

anchor(x) in V union E union F union C
```

Every claimed object must declare its carrier anchor. A spinor, Hopf torus
chart, quaternion orientation, terrain action, stage placement, substage action,
or flux boundary current that has no finite PEPS3D anchor is not admitted as
nonclassical manifold evidence.

For a lattice site v:

```text
physical state:
  psi_(v,s) in C^2, ||psi_(v,s)|| = 1

finite probe response:
  p_(v,a) = <psi_(v,s)| E_a |psi_(v,s)>

local tensor:
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

where:

```text
a = finite physical/probe/spinor index
alpha_* = finite virtual bond indices
```

For an edge e = (u,v):

```text
transport:
  U_(uv,s) or channel Phi_(uv,s)

N01 witness:
  Phi_(uv) o Phi_(vw) != Phi_(vw) o Phi_(uv)
```

For a shell:

```text
Shell_k = finite set of sites/faces with q_shell(k)

boundary response:
  R_alpha(Psi_s, boundary, engine, shell)

alpha in {i,j,k}
```

The contraction readout must be finite:

```text
boundary reduced response = contract finite boundary tensors
not full dense-state closure unless explicitly fenced as smoke/control
```

For 64 substages, the stricter manifold-cell target is:

```text
c = (engine_type, loop_field, terrain, operator_slot)

T_c[
  alpha_x_minus,
  alpha_x_plus,
  alpha_y_minus,
  alpha_y_plus,
  alpha_z_minus,
  alpha_z_plus,
  a
]

pi_stage(c) = (engine_type, loop_field, terrain)
```

The 16-stage-site plus four operator-row scaffold is an inventory, not a
64-cell manifold embedding. A valid 64-substage claim must either give each
substage its own PEPS3D cell/tensor/channel action, or give an explicit
projection from a richer PEPS3D cell carrier to the 16 stage placements.

## 9. Blocked Flux Target Spec

Flux is not executable from this ledger while `foundation_closed=false`. This
section is a blocked target specification only. A new flux row must first cite
lower receipts for finite PEPS3D-carried spinor cells, nested Hopf tori, any
quaternionic map/invariant it uses, sheet cover, terrain/loop placements, and
64 substage-cell embedding.

Flux target position:

```text
finite PEPS3D-carried spinor/quaternion shell carrier
  -> L/R terrain placements and engine token schedule
  -> BLOCKED FLUX CANDIDATE
  -> Xi / rho_AB / Phi0 / Axis0
```

Candidate object, not admitted evidence:

```text
J_flux(engine, shell, boundary)
  = i J_i + j J_j + k J_k

J_alpha =
  R_alpha(Psi_R, engine, boundary, shell)
  - R_alpha(Psi_L, engine, boundary, shell)

alpha in {i,j,k}
```

Admission tests required before queueing or accepting flux:

```text
F01:
  finite sites
  finite probes
  finite boundary contraction
  finite engine schedule

N01:
  order swap changes J_flux
  commuting/order-erased control collapses

sheet-bound:
  L/R sheet erase collapses or materially changes J_flux

shell-bound:
  shell-time reversal changes j/k components

engine-bound:
  Type 1 and Type 2 schedules produce distinct flux response

topology-bound:
  topology freeze kills the topology-mutation part of J_flux
```

Flux is not admitted if it is only:

```text
right scalar - left scalar
sampled boundary gap
Axis0 sign helper
EngineCore scalar
NumPy dense-state toy
Pauli/Bloch primitive vector current
```

## 10. Blocked Axis0 Target Spec

Axis0 is downstream of flux and remains blocked while
`flux_queue_allowed=false` or `axis0_queue_allowed=false`.

```text
A0 = directional signed QIT/FEP entropy gradient
     read over finite spinor-shell histories and flux transport
```

One candidate finite form:

```text
F_QIT =
  D(rho_actual || rho_recovered)
  + C_transition
  + H_path
  - I_gain
  - R_recovery

A0 = Delta F_QIT / Delta lambda
```

Sign convention:

```text
A0 < 0  homeostatic compression
A0 > 0  allostatic reconfiguration pressure
A0 ~= 0 neutral, saturated, wrong cut, or branch-count artifact
```

Axis0 is not allowed to repair a missing flux/manifold foundation. No Axis0 scout,
queue row, summary, or result may be treated as progress on the manifold
foundation unless it cites the lower receipt chain and keeps the Axis0 claim
ceiling downstream.

## 11. Tool Requirements

Aligned load-bearing nonclassical tools:

```text
PyTorch complex tensors and autograd
torch-native tensor-network contraction for PEPS3D carrier
finite probe/effect algebra checks
Weyl-Heisenberg finite operator algebra
quaternion/Clifford algebra checks
z3/cvc5 for finite constraint admissibility
sympy for symbolic sanity checks
rustworkx/XGI/TopoNetX/GUDHI for graph/topology controls
PyG only for graph neural adapter/scout rows
```

Adapter/control only unless separately admitted:

```text
NumPy
SciPy
EngineCore
Bloch/Pauli primitive axes
Cartesian x/y/z face sampling
dense full-state closure
quimb/cotengra if NumPy-backed and used as load-bearing evidence
```

Any nonclassical formal scout that imports NumPy, calls `.numpy()`, or depends
on local NumPy-backed source must be demoted, blocked, or fenced as an adapter
control.

## 12. Current Formal Blocker

The missing lower object before any new flux or Axis0 work is:

```text
source-conformant torch-native spinor/quaternion PEPS3D carrier with admitted
finite maps, controls, and substage cells
```

with all of:

```text
finite probe/effect quotient
PEPS3D carrier active from the first finite carrier/probe step
spinor local state on finite PEPS3D anchors
nested Hopf tori on the spinor carrier
quaternion shell orientation map/invariant if quaternion language is used
L/R chiral sheets on the same PEPS3D-carried spinor shell
8 terrain generators
16 stage placements as sheet/loop/terrain/token/sign cells
ordered token table
Axis5 family
Axis6 precedence/action side
64 substage cells with local tensor/channel/action evidence
finite PEPS3D spinor-network contraction/readout controls
```

Flux is a later candidate derived from that lower object. Axis0 is later still:
only after flux, Xi, and Phi0/cut-state evidence are carried on the same finite
spinor/quaternion PEPS3D substrate.

Until that exists, the correct classification is:

```text
flux: derived target, blocked until lower finite maps and cells close
Axis0: downstream readout target, blocked until flux and Xi are carried
physics: blocked
```
