# Root To Spinor PEPS3D Manifold

Status: working math spine and admission grammar, not an admitted final layer
stack.

## 1. Root Object

The first geometry allowed by the two root constraints is not a sphere, vector
space, Pauli triple, density matrix, or Cartesian shell. The first object is
finite operational distinguishability under noncommuting admissible operations.

Start with finite states/configurations and finite probes/effects:

```text
S = finite admissible state/configuration set
P = finite admitted probe/effect family

s1 ~_P s2 iff for every p in P, p(s1) = p(s2)

Q_P = S / ~_P
```

The roots are:

```text
F01_FINITUDE:
  finite sites
  finite probes/effects
  finite operators
  finite paths/histories
  finite carrier dimension

N01_NONCOMMUTATION:
  A o B != B o A in general
  A rho != rho A in general
  probe identity can depend on operation order
```

This is the first geometry in the strict sense: a finite quotient/probe
geometry. It gives identity relative to active probes and distinguishes order
only when an order witness survives controls.

## 2. Finite Effect And Response Layer

The current best concrete substrate candidate is finite effects:

```text
E = {E_i}
0 <= E_i <= I
sum_i E_i = I

p_i(rho) = Tr(E_i rho)
```

A SIC/POVM or other finite informationally complete family can act as a
concrete probe family. A Weyl-Heisenberg pair gives a finite noncommuting order
witness:

```text
X Z = omega Z X
```

The important point is not "use SIC forever." The point is that the root
carrier is a finite named effect-response structure, not a visual chart.

## 3. PEPS3D Begins At First Carrier Admission

For new nonclassical manifold work, the finite response quotient must be placed
on a finite PEPS3D spinor-network carrier immediately:

```text
K_0 = (V, E, F, C)

V = finite sites
E = finite bonds
F = finite faces
C = finite cells

T_v[a_v, {b_e}, {f}, {c}] = local tensor at site v
```

`K_0` is not proof of a layer. It is the finite carrier anchor required so
later spinor, Hopf, terrain, operator, flux, and Axis0 objects cannot float as
labels.

Every candidate step must define:

```text
domain D_i
finite PEPS3D carrier slice K_i
map f_i : D_i -> D_(i+1) or invariant I_i(D_i)
output object O_i on K_i
F01 witness
N01 witness
negative/control condition
blocked downstream consumers
receipt or blocked-reason path
```

## 4. Spinor Carrier

The local nonclassical carrier is a spinor on finite sites/cells:

```text
psi_v in S^3 subset C^2
||psi_v|| = 1
```

Use the Hopf chart only after the carrier is declared:

```text
psi_s(phi, chi; eta) =
  [ exp(i(phi + chi)) cos eta,
    exp(i(phi - chi)) sin eta ]^T

s in {L, R}
eta in [0, pi/2]
phi, chi in [0, 2pi)
```

Density is a readout/carrier adapter:

```text
rho_v = psi_v psi_v^dagger
```

It is useful and often necessary, but it is not the whole geometry. If a sim
only carries `rho` and cannot reconstruct which spinor/Hopf/Weyl information is
load-bearing or intentionally quotiented, it is a density/readout sim, not a
full spinor-manifold sim.

## 5. Nested Hopf Tori

The Hopf connection and torus stack must be explicit:

```text
A_Hopf = -i psi^dagger d psi
       = d phi + cos(2 eta) d chi

T_eta(k,v) = {
  psi_v(phi, chi; eta_k)
}
```

The finite shell stack is:

```text
E_eta = finite shell index set
eta_k in [0, pi/2] for k in E_eta
pi_shell(v,k,phi,chi) = (v,k)
```

Minimum controls:

```text
finite-shell erased or collapsed
Hopf connection omitted or flattened
shell order reversed where order matters
PEPS3D carrier anchor removed
```

Without those controls, "nested Hopf tori" is only vocabulary.

## 6. Loop Fields

The two primary loop fields differ by density visibility:

```text
fiber loop:
  gamma_f^s(u) = psi_s(phi_0 + u, chi_0; eta_0)
  rho_f^s(u) = rho_f^s(0)

lifted-base loop:
  gamma_b^s(u) =
    psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)
  A_Hopf(dot gamma_b^s) = 0
  rho_b^s(u) changes with u
```

This distinction is one reason Bloch/density-only summaries leak classical
readings: the fiber path can be invisible to density while still being real in
the spinor/Hopf carrier.

## 7. Left And Right Weyl Sheets

The Weyl sheet cover is on the same finite spinor carrier:

```text
H_L = +H_0
H_R = -H_0

rho_dot_L = -i [H_L, rho_L]
rho_dot_R = -i [H_R, rho_R]
```

Left/right is not just a label for two copies. It changes the sign of the local
Hamiltonian flow and therefore the placement/readout story.

## 8. Terrain Generators And Placements

Terrain generator families sit after spinor/Hopf/Weyl carrier work:

```text
tau in {Se, Ne, Ni, Si}
s in {L, R}
ell in {fiber, base}

X_(tau,s) = terrain generator on sheet s
Y_ell = loop field
```

A placement is:

```text
placement = (s, ell, tau, X_(tau,s), Y_ell, source_token, axis6_sign)
```

It is not a terrain word alone. It is a constrained local object on a finite
carrier with a loop field and sheet.

## 9. Operator Substage Cells

An operator substage is a fiber over a stage placement:

```text
cell c = (engine_type, loop_field, terrain, operator_slot)

T_c = finite PEPS3D-carried local tensor/channel/action
```

The corrected target is 64 finite cell actions across the paired cycle:

```text
2 engine types
x 8 macro stages per engine
x 4 operator substages per macro stage
= 64 substage actions
```

A row label is not enough. Each cell must carry local spinor/Hopf position,
probe response, tensor/channel action, Axis6 order witness, and any quaternion
map/invariant if quaternion language is used.

## 10. Downstream Boundaries

The following remain blocked until the lower chain is admitted:

```text
flux finalization
Xi bridge closure
Phi0 closure
Axis0 theorem
Holodeck/FEP proof
physics claims
attractor-basin convergence
```

The lower chain may produce many useful formal scouts before it is closed. Those
scouts should be used as fuel, not promoted into canon by summary wording.

