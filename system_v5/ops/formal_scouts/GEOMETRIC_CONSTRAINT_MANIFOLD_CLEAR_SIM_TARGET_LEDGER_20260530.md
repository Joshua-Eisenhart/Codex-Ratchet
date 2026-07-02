# Geometric Constraint Manifold: Layered Sim Blueprint

Status: planning and sim-target document.

This is not a completion claim. It does not select a final G-structure. It
does not admit stacking, flux, Xi, Phi0, Axis0, FEP, physics, gravity, or final
manifold closure.

This file replaces the earlier numbered-row ledger. The old row IDs were a
mistake because they made labels look like objects. In this file, every project
term is bound to candidate mathematical objects, finite maps, domains,
codomains, controls, and existing repo surfaces where those surfaces exist.

## Binding Rule

Project words are allowed only in this form:

```text
project term
  candidate mathematical object(s)
  carrier acted on
  finite map
  domain
  codomain
  controls that kill wrong interpretations
  existing sim surface, if present
```

Forbidden form:

```text
terrain = Funnel on left fiber
```

Allowed form:

```text
Funnel, used as shorthand only:
  candidate generator X_F,L on left Weyl density states
  placed along the finite fiber path gamma_f,L
  map rho_next = CPTP_step[X_F,L, gamma_f,L](rho)
  controls erase the generator, erase the path, swap the sheet, or commute the
  history and must change the readout.
```

## Current Repo Surfaces Read For This Blueprint

These are not proof of completion. They are the current local source surfaces
that this blueprint is grounded against.

```text
system_v5/ops/formal_scouts/layer_full_spinor_network_individual_runner.py
```

This is shared plumbing for separate full-spec layer scouts. It defines existing
repo layer configs named L0 through L8, uses site-count stress values
8/16/32/64 with finite 3D shapes, uses bond_dim 4, and imports torch, quimb,
cotengra, opt_einsum, clifford, sympy, z3, cvc5, rustworkx, XGI, TopoNetX,
GUDHI, PyG, geomstats, and e3nn. In this blueprint those site counts are
existing stress sizes, not universal "depth" and not qubits.

```text
system_v5/ops/formal_scouts/sim_l4_terrain_generator_full_spinor_network_layer_probe.py
system_v5/ops/formal_scouts/sim_l5_operator_substage_full_spinor_network_layer_probe.py
```

These are wrappers around the shared runner. They do not by themselves define
the whole manifold. They are existing formal-scout entry points for one layer at
a time, with downstream consumers locked.

```text
system_v5/ops/formal_scouts/sim_weyl_spinor_layer_mps_peps2d_peps3d_admission_probe.py
```

This is an existing source-native Weyl spinor layer candidate across MPS,
PEPS2D, and PEPS3D carrier views. It explicitly says it does not unlock
stacking, flux, Xi/Phi0, Axis0, FEP, physics, or final manifold admission.

```text
system_v5/ops/formal_scouts/sim_jax_geometry_full_network_targets_probe.py
system_v5/ops/formal_scouts/results/jax_geometry_full_network_targets_20260530/
```

This is an existing JAX/PyTorch geometry-target batch. It repaired a prior
weakness by adding MPS, PEPS2D, PEPS3D carrier checks, target-specific transport
coefficients, JAX x64 versus PyTorch parity, QIT readouts, and topology/proof
controls. It is still bounded formal-scout evidence, not G-structure selection
or layer completion.

```text
system_v5/ops/formal_scouts/sim_m_rpf_l4_terrain_channel_shell_object_preservation_probe.py
```

This is an existing M_RPF shell-object preservation scout for the terrain/channel
row. It preserves the order:

```text
Omega_r branches
  -> compatibility weights
  -> terrain/channel adapter
  -> compression
  -> rho_present
  -> outward_record
  -> derived readouts
```

That source still contains compact terrain labels. This blueprint expands those
labels into candidate math and should be treated as the clearer planning
surface.

## Root Constraints

These are not manifold layers. They are the admission constraints every layer,
candidate geometry, readout, and stack test must satisfy.

### F01: finite carrier, probes, operators, and paths

```text
dim(H) < infinity
V, E, F, C finite
probe set P finite
operator/channel registry A finite
path/history registry H_path finite
capacity budget finite
```

Allowed finite quantum states:

```text
rho in D(H)
D(H) = {rho : rho = rho_dagger, rho >= 0, Tr(rho) = 1}
```

### N01: noncommuting or order-sensitive action

For some admissible finite maps A and B:

```text
A o B != B o A
```

or for an operator A and state rho:

```text
[A, rho] = A rho - rho A != 0
```

Order tests are not optional later decoration. They are how the manifold avoids
collapsing into a commutative label table.

## Shared Finite Carrier

The base finite object is:

```text
K = (V, E, F, C)
```

where:

```text
V = finite sites/cells
E = finite bonds/edges
F = finite faces or shell patches
C = finite constraints, probes, operators, channels, or admissible paths
```

At site v and sheet s in {L, R}:

```text
psi_v,s in C^2
||psi_v,s|| = 1
rho_v,s = psi_v,s psi_v,s_dagger
```

For an edge e = (u, v), the edge can carry an entangled or compatible two-site
state:

```text
rho_uv,st in D(C^2 tensor C^2)
```

The dynamic carrier state is:

```text
State(t) =
  (
    psi_v,L(t), psi_v,R(t),
    rho_v,L(t), rho_v,R(t),
    rho_uv,st(t),
    w_e(t),
    chi_e(t),
    shell_index k(t),
    torus_leaf eta_v(t),
    connection A_v(t),
    transport U_gamma(t),
    possibility weights p_r(omega,t)
  )
```

The carrier must evolve. A static invariant check is only a diagnostic. A layer
sim needs either:

```text
State(t + dt) = F(State(t), probe_t, theta)
```

or:

```text
d State / dt = X(State, t, theta)
```

## Computational Carrier Views

The source object is the spinor network above. Tensor-network tools are
computational carrier views of that object, not the ontology.

### MPS view

Use for one-dimensional paths, ordered histories, boundary strings, or shell
loops:

```text
Psi(i_1,...,i_N) =
  sum_{alpha_1,...,alpha_{N-1}}
    A_1[i_1]_{alpha_1}
    A_2[i_2]_{alpha_1,alpha_2}
    ...
    A_N[i_N]_{alpha_{N-1}}
```

Native scale variables:

```text
N_path       path sites
chi_mps      MPS bond dimension
N_histories  finite history count
```

### PEPS2D view

Use for finite shell sheets, torus leaves, and two-dimensional local patches:

```text
Psi({i_v}) =
  Contract over edge bonds of A_v[i_v]_{left,right,up,down}
```

Native scale variables:

```text
N_eta       torus leaves
N_fiber     fiber samples
N_base      base-lift samples
chi_peps2d  PEPS2D bond dimension
```

### PEPS3D view

Use for finite three-dimensional shell/cell support. This is the repo's
first-carrier anchor requirement for new nonclassical manifold claims, but it
must mean an actual finite spinor-network carrier view, not a scalar label.

```text
Psi({i_v}) =
  Contract over 3D nearest-neighbor or cell-complex bonds of
  A_v[i_v]_{x-,x+,y-,y+,z-,z+}
```

Native scale variables:

```text
N_shell       shell levels
N_eta         torus leaves per shell
N_fiber       fiber samples
N_base        base-lift samples
N_sites       finite sites
chi_peps3d    PEPS3D bond dimension
N_boundary    boundary sites/cells
```

Existing repo stress sizes such as 8/16/32/64 are only a current finite
site-count ladder. They are not qubits unless a sim explicitly says Hilbert
dimension equals 2^n and actually uses that Hilbert space.

## The Layered Geometric Constraint Manifold

The manifold candidate is a dependency-ordered stack of finite maps over the
shared carrier. The layers below are proposed sim targets, not proven canon.

Each layer must be simulated independently before it is used for stacking.

### Layer: finite response and distinguishability quotient

Purpose:

Build the first finite geometry from distinguishability under probes.

Candidate math:

```text
P = {E_a}_{a=1..m}
E_a >= 0
sum_a E_a = I
```

For state rho_x:

```text
r_P(x) = (Tr(E_1 rho_x), ..., Tr(E_m rho_x))
```

Define finite equivalence:

```text
x ~_P y iff ||r_P(x) - r_P(y)|| <= epsilon
```

The quotient carrier is:

```text
Q_P = X / ~_P
```

Finite map:

```text
FiniteResponseQuotient:
  (finite state registry X, finite probes P, tolerance epsilon)
  -> (quotient cells Q_P, response vectors r_P, noncollapsed controls)
```

Controls:

```text
remove a load-bearing probe E_a
replace noncommuting probes with commuting probes
scramble response vectors
make all response vectors equal
```

Existing related surfaces:

```text
sim_l0_response_quotient_full_spinor_network_layer_probe.py
sim_l0_response_quotient_mps_peps2d_peps3d_depth_probe.py
sim_jax_native_l0_response_effect_path_quotient_layer_probe.py
```

### Layer: source-native finite spinor network

Purpose:

Represent the manifold fabric as finite left/right spinor states and finite
edge/cell compatibility, before any downstream readout.

Candidate math:

```text
psi_v,s in C^2
||psi_v,s|| = 1
rho_v,s = psi_v,s psi_v,s_dagger
s in {L, R}
```

Finite edge compatibility:

```text
w_uv(t) = f(rho_u,L, rho_u,R, rho_v,L, rho_v,R, edge metadata)
0 <= w_uv <= 1
```

Two-site cut state:

```text
rho_uv in D(C^2 tensor C^2)
Tr(rho_uv) = 1
rho_uv >= 0
```

Finite map:

```text
SpinorNetworkStep:
  (K, {psi_v,s(t)}, {rho_uv(t)}, {w_e(t)}, local actions A)
  -> ({psi_v,s(t+dt)}, {rho_uv(t+dt)}, updated weights, cut readouts)
```

Controls:

```text
erase phases
replace edge states by product states
randomize edges while preserving labels
use dense global state without local carrier provenance
```

Existing related surfaces:

```text
layer_full_spinor_network_individual_runner.py
sim_l1_spinor_density_carrier_layer_probe.py
sim_carrier_spinor_density_probe.py
sim_carrier_torch_complex_spinor_probe.py
sim_dual_engine_quimb_peps3d_spinor_network_carrier_probe.py
```

### Layer: literal shell possibility field

Purpose:

Make the retrocausal possibility object explicit before Axis0, FEP, flux, or
physics claims.

For event x and finite shell radius r:

```text
Sigma_r(x) = finite shell/cell subset of K at shell order r
Omega_r(x) = finite set of admissible future refinements on Sigma_r(x)
p_r(omega) >= 0
sum_{omega in Omega_r} p_r(omega) = 1
```

Boundary state:

```text
rho_B,r in D(H_B,r)
```

Interior-boundary compatible state:

```text
rho_IrBr in D(H_I,r tensor H_B,r)
Tr_I(rho_IrBr) = rho_B,r
```

Admissible completions:

```text
A(r) =
  {rho_IrBr :
     Tr_I(rho_IrBr) = rho_B,r
     and rho_IrBr satisfies finite constraints/channels}
```

Compression into present:

```text
C_r({rho_omega, p_r(omega)}_{omega in Omega_r})
  = rho_present,r
```

Outward record:

```text
Record_r =
  (r, Sigma_r, selected/surviving branch data, boundary readouts,
   compatibility weights, controls)
```

Finite map:

```text
ShellPossibilityStep:
  (K, event x, Sigma_r(x), Omega_r(x), rho_omega, p_r(omega), C_r)
  -> (rho_present,r, outward_record,r, shell readouts, failed controls)
```

Controls:

```text
erase shell radius r
erase future-inward and past-outward orientation
scramble Omega_r independently of Sigma_r
uniformize p_r(omega)
compress before compatibility weighting
replace rho_IrBr by product state
```

Existing related surfaces:

```text
sim_retrocausal_possibility_field_seed_probe.py
sim_m_rpf_l0_response_shell_object_preservation_probe.py
sim_m_rpf_l1_boundary_environment_shell_object_preservation_probe.py
sim_m_rpf_cross_row_order_closure_probe.py
sim_m_rpf_post_stack_stress_probe.py
```

### Layer: Hopf, projective base, nested tori, and transport

Purpose:

Give the spinor network internal phase/fiber/base geometry and finite transport
paths without using a hidden Cartesian center.

Unit spinor:

```text
psi(phi, chi, eta) =
  [
    exp(i(phi + chi)) cos(eta),
    exp(i(phi - chi)) sin(eta)
  ]^T
```

Normalization:

```text
psi_dagger psi = 1
psi in S3 subset C^2
```

Projective base:

```text
[psi] in CP1
```

Hopf fiber:

```text
psi ~ exp(i alpha) psi
fiber = U(1) orbit of psi
```

Nested torus leaf:

```text
T_eta = {(phi, chi, eta) : phi, chi in [0, 2 pi)}
```

Hopf connection:

```text
A_H = -i psi_dagger d psi
```

For the parameterization above:

```text
A_H = d phi + cos(2 eta) d chi
```

Fiber path:

```text
gamma_f(u) = psi(phi_0 + u, chi_0, eta_0)
```

Base-lift path:

```text
gamma_b(u) = psi(phi_0 - cos(2 eta_0) u, chi_0 + u, eta_0)
```

Parallel-lift condition:

```text
A_H(dot gamma_b) = 0
```

Discrete holonomy:

```text
U_gamma = product_{m=1..M} exp(-i integral_{edge_m} A_H)
```

Finite map:

```text
HopfTransportStep:
  (psi_v,s, eta_v, gamma in {fiber, base_lift}, discrete connection A_H)
  -> (transported psi_v,s, transported rho_v,s, holonomy U_gamma, gaps)
```

Controls:

```text
erase fiber phase
replace base-lift by arbitrary path
set A_H = 0
collapse all eta leaves
swap fiber and base-lift without changing output
```

Existing related surfaces:

```text
sim_l7_hopf_shell_full_spinor_network_layer_probe.py
sim_l7_hopf_shell_mps_peps2d_peps3d_depth_probe.py
sim_l5_nested_hopf_tori_leaf_family_layer_probe.py
sim_jax_native_geometry_hopf_fibration_s3_to_s2_probe.py
sim_jax_native_geometry_nested_hopf_tori_probe.py
```

### Layer: Clifford, quaternion, spin, and twistor local structure

Purpose:

Test whether additional local algebraic geometry is load-bearing for the
spinor/shell carrier.

Quaternion/SU(2) candidate:

```text
q = a + b i + c j + d k
||q|| = 1
q and -q map to the same SO(3) rotation
```

Rotor action:

```text
R_q(v) = q v q^{-1}
```

Clifford module candidate:

```text
gamma_i gamma_j + gamma_j gamma_i = 2 g_ij I
```

Chirality operator when admitted:

```text
gamma5^2 = I
P_L = (I - gamma5) / 2
P_R = (I + gamma5) / 2
P_L P_R = 0
```

Twistor incidence candidate:

```text
Z = (omega^A, pi_A')
omega^A = i x^{AA'} pi_A'
```

Finite no-continuum incidence version:

```text
I_uv = omega_u^A pi_{v,A}
```

Finite map:

```text
LocalAlgebraicStructureStep:
  (spinor network state, candidate algebra object, finite action registry)
  -> (transformed spinors/densities, invariant residuals, controls)
```

Controls:

```text
break Clifford anticommutation
replace quaternion rotor by arbitrary matrix
erase chirality projectors
make twistor incidence independent of spinor state
```

Existing related surfaces:

```text
sim_l3_clifford_quaternion_full_spinor_network_layer_probe.py
sim_jax_native_l3_quaternion_clifford_orientation_layer_probe.py
sim_geom_twistor_incidence_deep_probe.py
sim_jax_native_geometry_twistor_incidence_spinor_geometry_probe.py
```

### Layer: left/right Weyl sheet cover

Purpose:

Represent left and right Weyl states as related but non-identical sheeted
spinor dynamics.

Left and right sheet states:

```text
psi_v,L, psi_v,R in C^2
rho_v,L = psi_v,L psi_v,L_dagger
rho_v,R = psi_v,R psi_v,R_dagger
```

Candidate generators:

```text
H_L = +H_0
H_R = -H_0
```

Unitary part:

```text
d rho_v,L / dt = -i [H_L, rho_v,L]
d rho_v,R / dt = -i [H_R, rho_v,R]
```

Sheet non-equivalence readout:

```text
Delta_LR =
  || Observable_L(after path/action) - Observable_R(after mirrored path/action) ||
```

Finite map:

```text
WeylSheetStep:
  (K, psi_v,L, psi_v,R, H_L, H_R, path/action registry)
  -> (rho_L(t+dt), rho_R(t+dt), chirality gaps, mirror controls)
```

Controls:

```text
force H_L = H_R
swap sheet labels without changing action
erase gamma5/chirality metadata
make left and right product-identical under all probes
```

Existing related surfaces:

```text
sim_l2_weyl_spinor_full_spinor_network_layer_probe.py
sim_l2_weyl_spinor_chirality_mps_peps2d_peps3d_depth_probe.py
sim_weyl_spinor_layer_mps_peps2d_peps3d_admission_probe.py
sim_left_right_weyl_density_terrain_loop_placement_mirror_non_equivalence_probe.py
```

### Layer: local Weyl dynamical-law candidates

Purpose:

Bind the eight terrain words to candidate equations on left/right Weyl density
states. The names are shorthand only.

Shared dissipator:

```text
D[L](rho) =
  L rho L_dagger
  - 1/2 (L_dagger L rho + rho L_dagger L)
```

Shared finite integrator:

```text
rho(t + dt) =
  NormalizeDensity(rho(t) + dt X(rho(t)))
```

or, when represented as a channel:

```text
rho(t + dt) = sum_j K_j rho(t) K_j_dagger
sum_j K_j_dagger K_j = I
```

The four left-sheet candidate laws:

```text
Funnel shorthand:
  X_F,L(rho) =
    -i epsilon_F [H_L, rho]
    + gamma_F sum_j D[n_j . sigma](rho)
  candidate meaning: dissipative contraction/sink on left sheet.

Vortex shorthand:
  X_V,L(rho) =
    -i [H_L + lambda_V G_V, rho]
    + epsilon_V D[L_V](rho)
  candidate meaning: circulation with weak dissipation on left sheet.

Pit shorthand:
  X_P,L(rho) =
    gamma_P D[sigma_-](rho)
    - i epsilon_P [H_L, rho]
  candidate meaning: ladder-attractor/sink on left sheet.

Hill shorthand:
  X_H,L(rho) =
    -i [K_L, rho]
    + kappa_H (sum_a P_a rho P_a - rho)
  where P_a P_b = delta_ab P_a and sum_a P_a = I.
  candidate meaning: retained projector strata on left sheet.
```

The four right-sheet candidate laws:

```text
Cannon shorthand:
  X_C,R(rho) =
    -i epsilon_C [H_R, rho]
    + gamma_C D[L_release](rho)
  candidate meaning: release/source-projection candidate on right sheet.

Spiral shorthand:
  X_Sp,R(rho) =
    -i [H_R + lambda_Sp G_Sp, rho]
    + epsilon_Sp D[L_Sp](rho)
  candidate meaning: opposite-sheet circulation candidate.

Source shorthand:
  X_So,R(rho) =
    gamma_So D[sigma_+](rho)
    - i epsilon_So [H_R, rho]
  candidate meaning: ladder-emitter/source on right sheet.

Citadel shorthand:
  X_Ci,R(rho) =
    -i [K_R, rho]
    + kappa_Ci (sum_a Q_a rho Q_a - rho)
  where Q_a Q_b = delta_ab Q_a and sum_a Q_a = I.
  candidate meaning: protected projector strata on right sheet.
```

Finite map:

```text
WeylLawStep:
  (sheet s, rho_v,s(t), candidate generator X_name,s, dt)
  -> (rho_v,s(t+dt), generator residuals, basin/readout changes)
```

Controls:

```text
replace X_name,s by zero generator
replace dissipative law by unitary-only law
swap left generator onto right sheet without sign/context change
force all eight laws to share identical parameters and outputs
```

Existing related surfaces:

```text
sim_l4_terrain_generator_full_spinor_network_layer_probe.py
sim_l4_terrain_channel_generator_layer_probe.py
sim_jax_native_l4_terrain_channel_generator_layer_probe.py
sim_terrain_gksl_dissipator_dual_backend_torch_jax_probe.py
sim_shell_terrain_parametric_family_sweep_probe.py
```

### Layer: placement of local laws on finite paths

Purpose:

Place each sheet's candidate laws on the two finite Hopf paths. This is where
the old numbered rows were wrong: the placement is a map, not a new label.

For sheet s and path ell:

```text
ell in {fiber, base_lift}
gamma_ell,s = finite sampled path on the sheeted Hopf carrier
U_ell,s = discrete transport along gamma_ell,s
```

Path-placed law:

```text
PlacedStep(name, s, ell):
  rho_pre = U_ell,s rho_v,s U_ell,s_dagger
  rho_next = CPTP_or_GKSL_step[X_name,s](rho_pre)
  return (rho_next, holonomy gap, law gap, cut readouts)
```

The required independent placements are:

```text
left sheet, fiber path, Funnel shorthand:
  use X_F,L and gamma_f,L in PlacedStep(Funnel, L, fiber).

left sheet, fiber path, Vortex shorthand:
  use X_V,L and gamma_f,L in PlacedStep(Vortex, L, fiber).

left sheet, fiber path, Pit shorthand:
  use X_P,L and gamma_f,L in PlacedStep(Pit, L, fiber).

left sheet, fiber path, Hill shorthand:
  use X_H,L and gamma_f,L in PlacedStep(Hill, L, fiber).

left sheet, base-lift path, Funnel shorthand:
  use X_F,L and gamma_b,L in PlacedStep(Funnel, L, base_lift).

left sheet, base-lift path, Vortex shorthand:
  use X_V,L and gamma_b,L in PlacedStep(Vortex, L, base_lift).

left sheet, base-lift path, Pit shorthand:
  use X_P,L and gamma_b,L in PlacedStep(Pit, L, base_lift).

left sheet, base-lift path, Hill shorthand:
  use X_H,L and gamma_b,L in PlacedStep(Hill, L, base_lift).

right sheet, fiber path, Cannon shorthand:
  use X_C,R and gamma_f,R in PlacedStep(Cannon, R, fiber).

right sheet, fiber path, Spiral shorthand:
  use X_Sp,R and gamma_f,R in PlacedStep(Spiral, R, fiber).

right sheet, fiber path, Source shorthand:
  use X_So,R and gamma_f,R in PlacedStep(Source, R, fiber).

right sheet, fiber path, Citadel shorthand:
  use X_Ci,R and gamma_f,R in PlacedStep(Citadel, R, fiber).

right sheet, base-lift path, Cannon shorthand:
  use X_C,R and gamma_b,R in PlacedStep(Cannon, R, base_lift).

right sheet, base-lift path, Spiral shorthand:
  use X_Sp,R and gamma_b,R in PlacedStep(Spiral, R, base_lift).

right sheet, base-lift path, Source shorthand:
  use X_So,R and gamma_b,R in PlacedStep(Source, R, base_lift).

right sheet, base-lift path, Citadel shorthand:
  use X_Ci,R and gamma_b,R in PlacedStep(Citadel, R, base_lift).
```

Controls:

```text
path erased: U_ell,s = I
law erased: X_name,s = 0
path swapped: gamma_f,s replaced by gamma_b,s
sheet swapped: L context replaced by R context or R by L
order collapsed: law after path forced equal to path after law
```

Existing related surfaces:

```text
sim_left_right_weyl_density_terrain_loop_placement_mirror_non_equivalence_probe.py
sim_shell_terrain_exact_hopf_loop_harness_probe.py
sim_shell_terrain_operator_composition_order_probe.py
sim_m_rpf_l4_terrain_channel_shell_object_preservation_probe.py
```

### Layer: local operator and channel action families

Purpose:

These are not geometry by themselves. They are finite local action families on
the geometric carrier. They become part of the constraint manifold only because
the manifold includes admissible local motion and noncommuting path order.

Projector/pinching:

```text
Pinch_P(rho) = sum_a P_a rho P_a
P_a P_b = delta_ab P_a
sum_a P_a = I
```

Unitary transport:

```text
U_A(theta) = exp(-i theta A)
rho -> U_A rho U_A_dagger
```

CPTP channel:

```text
Phi(rho) = sum_j K_j rho K_j_dagger
sum_j K_j_dagger K_j = I
```

Lindblad generator:

```text
L(rho) =
  -i [H, rho]
  + sum_j D[L_j](rho)
```

Order gap:

```text
Gap(A, B; rho) =
  || A(B(rho)) - B(A(rho)) ||
```

Finite map:

```text
LocalActionStep:
  (rho_v,s, local operator/channel registry A, path/order h)
  -> (rho_v,s after action, order gaps, channel validity, controls)
```

Controls:

```text
commuting-only registry
non-CPTP channel
unitary-only replacement
operator label swap with identical matrix
```

Existing related surfaces:

```text
sim_l5_operator_substage_full_spinor_network_layer_probe.py
sim_l5_operator_substage_mps_peps2d_peps3d_depth_probe.py
sim_cptp_channel_family_8_16_32_64_dual_engine_probe.py
sim_dual_engine_operator_generality_commutation_graph_probe.py
```

### Layer: patch, gluing, and groupoid compatibility

Purpose:

Test whether local finite patches can be related without collapsing their
orientation, shell provenance, or local action order.

Finite groupoid:

```text
Obj(G) = finite patches/charts/cells
Arr(G) = admissible arrows g : a -> b
```

Composition:

```text
h o g is defined when target(g) = source(h)
```

Patch transition:

```text
T_ab : local data on patch a -> local data on patch b
```

Cocycle/closure condition on admissible overlaps:

```text
T_ac = T_bc o T_ab
```

up to a finite tolerance or declared obstruction:

```text
Residual_abc = ||T_ac - T_bc o T_ab||
```

Finite map:

```text
GluingStep:
  (patch states, overlap maps T_ab, finite groupoid arrows)
  -> (compatible glued object or blocked obstruction, residuals, controls)
```

Controls:

```text
erase arrow orientation
make all transitions identity
remove one overlap map
force noncomposable arrows to compose
```

Existing related surfaces:

```text
sim_l8_groupoid_gluing_full_spinor_network_layer_probe.py
sim_l8_groupoid_gluing_mps_peps2d_peps3d_depth_probe.py
sim_jax_native_l8_gluing_groupoid_layer_probe.py
```

## Cross-Layer Readouts, Not Layers

The following are not manifold layers. They are readouts that should run across
every relevant layer and geometry.

### Entropy and QIT readouts

State entropy:

```text
S(rho) = -Tr(rho log rho)
```

Reduced/cut entropy:

```text
rho_A = Tr_B(rho_AB)
S_A = S(rho_A)
```

Conditional entropy:

```text
S(A|B) = S(rho_AB) - S(rho_B)
```

Coherent information:

```text
I_c(A -> B) = S(rho_B) - S(rho_AB)
```

Mutual information:

```text
I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)
```

Conditional mutual information:

```text
I(A:C|B) = S(AB) + S(BC) - S(B) - S(ABC)
```

Quantum relative entropy:

```text
D(rho || sigma) = Tr rho (log rho - log sigma)
```

Log negativity:

```text
E_N(rho_AB) = log ||rho_AB^{T_B}||_1
```

Path entropy over finite histories:

```text
H_path = -sum_h p_h log p_h
```

Shell possibility entropy:

```text
H_Omega(r) = -sum_{omega in Omega_r} p_r(omega) log p_r(omega)
```

Capacity budget:

```text
S_boundary + H_path <= capacity_budget
```

These readouts must be attached to a finite state, finite cut, finite channel,
or finite path record. They are not allowed as free-floating scalar proxies.

Existing related surfaces:

```text
sim_l6_entropy_cut_full_spinor_network_layer_probe.py
sim_l6_entropy_cut_communication_mps_peps2d_peps3d_depth_probe.py
sim_entropy_family_admission_matrix_for_geometry_outputs_and_density_coercions_probe.py
sim_axis0_entropy_family_qit_fep_admission_bakeoff_probe.py
```

### Flux as derived current, not a standalone layer

Flux is a derived response of shell/transport/terrain changes.

Shell possibility current candidate:

```text
J_Omega(r -> r-1, t) =
  H_Omega(r,t) - H_Omega(r-1,t+dt)
```

Correlation current candidate:

```text
J_I(e,t) =
  I_e(t+dt) - I_e(t)
```

Transport current candidate:

```text
J_U(gamma,t) =
  Readout(U_gamma(t+dt) rho U_gamma(t+dt)_dagger)
  - Readout(U_gamma(t) rho U_gamma(t)_dagger)
```

Flux cannot be claimed until the terrain/transport/shell layer that produces
the change is present and controls show the current is not a scalar proxy.

### Xi, Phi0, and Axis0 as downstream bridge/readout

Xi is a bridge map:

```text
Xi:
  (K, shell stack, Omega_r, path history, transport, local states)
  -> rho_AB
```

Phi0 is a candidate projection/readout:

```text
Phi0:
  (rho_AB, shell-gradient metadata, order gaps, chirality metadata)
  -> expansion/binding polarity candidate
```

Candidate vector before scalarization:

```text
A0_raw =
  (
    Delta_r H_Omega,
    Delta_r S_boundary,
    Delta_r K_binding,
    order_gap,
    chirality_context
  )
```

Axis0 is not an independent geometry layer. It is a downstream polarity readout
that is wrong if Xi has forgotten shell radius, future-inward orientation,
Omega_r provenance, path order, or chirality context.

Existing related surfaces:

```text
sim_xi_phi0_axis0_readout_dependency_stability_gate_probe.py
sim_xi_phi0_boundary_capacity_cut_candidate_probe.py
sim_axis0_admitted_candidate_vector_bundle_ablation_probe.py
sim_qit_fep_axis0_path_integral_spinor_probe.py
```

### FEP / Holodeck as process/update consumer

FEP/Holodeck is not a manifold layer. It is a local update/process model that
can run on finite shell and cut states.

Finite histories:

```text
h = (a_1, ..., a_T)
K_h = K_T,a_T ... K_1,a_1
```

Evidence:

```text
Z_path =
  sum_h Tr[(E_A tensor I_B)
           (K_h tensor I_B)
           rho_AB
           (K_h_dagger tensor I_B)]
```

Posterior:

```text
tau_AB =
  sum_h (sqrt(E_A) tensor I_B)
        (K_h tensor I_B)
        rho_AB
        (K_h_dagger tensor I_B)
        (sqrt(E_A) tensor I_B)

rho_AB_given_E = tau_AB / Tr(tau_AB)
```

QIT free energy:

```text
F_Q(sigma_AB) =
  D(sigma_AB || tau_AB / Z_path) - log Z_path
```

This becomes admissible only when the finite shell/path/cut objects it consumes
are explicit.

## Separate Geometry Objects To Sim Beside The Layers

These are not all layers. They are geometry objects, carrier structures,
algebraic structures, or alternatives that can support, replace, or falsify
parts of the layer stack.

Each needs an independent standalone sim before being used in official stacking.

```text
S3 unit spinor carrier:
  object psi in C^2, ||psi||=1.
  invariant psi_dagger psi = 1.

CP1 projective Hopf base:
  object [psi] under psi ~ exp(i alpha) psi.
  invariant phase-equivalent states map to the same base point.

U(1) Hopf fiber:
  object phase orbit exp(i alpha) psi.
  invariant fiber action preserves rho = psi psi_dagger.

Hopf fibration S3 -> CP1:
  object projection pi(psi) = [psi].
  invariant pi(exp(i alpha) psi) = pi(psi).

Nested Hopf tori:
  object T_eta leaves inside S3.
  invariant eta-leaf structure remains distinguishable under admissible paths.

Clifford torus T2 in S3:
  object fixed eta torus with two angular directions.
  invariant two independent loop cycles survive controls.

Quaternion / SU(2) rotor:
  object unit quaternion q.
  invariant q and -q double-cover same SO(3) rotation.

Clifford modules:
  object gamma_i over finite metric g_ij.
  invariant gamma_i gamma_j + gamma_j gamma_i = 2 g_ij I.

Twistor incidence:
  object finite spinor incidence I_uv = omega_u^A pi_{v,A}.
  invariant incidence depends on spinor data, not labels alone.

Higher Hopf candidate S7 -> S4:
  object quaternionic Hopf candidate.
  invariant fiber/base projection survives finite sampling.

Contact / Sasakian S3:
  object contact form and Reeb direction candidate.
  invariant contact nondegeneracy survives finite discretization.

Spectral triple:
  object (A, H, D) finite algebra, Hilbert space, Dirac operator.
  invariant commutator [D,a] is bounded in finite registry.

Finite cell complex:
  object boundary maps partial_k.
  invariant partial_{k-1} partial_k = 0.
```

Existing related surfaces:

```text
sim_jax_geometry_full_network_targets_probe.py
sim_jax_native_geometry_s3_spinor_carrier_probe.py
sim_jax_native_geometry_cp1_fubini_study_probe.py
sim_jax_native_geometry_hopf_fibration_s3_to_s2_probe.py
sim_jax_native_geometry_nested_hopf_tori_probe.py
sim_jax_native_geometry_higher_hopf_s7_to_s4_probe.py
sim_jax_native_geometry_spectral_triple_probe.py
sim_jax_native_geometry_finite_cell_complex_boundary_probe.py
```

## G-Structure Candidates, Separate From Layers

A G-structure is a reduction of a frame bundle:

```text
F(M) -> P_G
G subset GL(n)
```

For finite sims, replace M by the finite carrier/patch complex and test whether
the candidate reduction preserves the needed structure.

```text
U(1):
  candidate for phase/fiber preservation.
  test connection A_H and fiber action.

SU(2) / Spin(3) / Sp(1):
  candidate for unit spinor/quaternion structure.
  test unit quaternions, spinor transport, double cover.

SO(3):
  ordinary orientation-frame candidate.
  test whether it is too weak because it forgets spin phase/chirality.

Pin / Spin:
  orientation and reflection/chirality cover candidate.
  test gamma/projector preservation.

Spin^c:
  spin plus U(1) phase candidate.
  test whether Hopf phase and spin structure coexist.

Symplectic:
  object omega, nondegenerate closed 2-form candidate.
  finite test J^2 = -I and omega-compatible transport.

Almost complex / Kahler:
  object J with J^2 = -I, metric compatibility, optional d omega = 0.
  test compatibility with projective and transport structures.

SU(n) / Calabi-Yau type:
  objects omega and holomorphic volume form Omega_form.
  test whether special-unitary reduction preserves more than U(n).

Sp(n) / hyperkahler:
  objects I,J,K with I^2=J^2=K^2=IJK=-1.
  test quaternionic compatibility with spinor carrier.

G2:
  object stable 3-form phi in 7D.
  test finite phi invariants and whether 7D structure is actually needed.

Spin(7):
  object Cayley 4-form Psi in 8D.
  test finite Spin(7) invariant and whether it preserves carrier data.

Seiberg-Witten-style gauge/spinor candidate:
  objects connection A and spinor psi with finite curvature equation analogue.
  test only as finite gauge/spinor compatibility, not continuum proof.

Hybrid Hopf-Spin-Twistor-Clifford reduction:
  object intersection or product of reductions that preserve shell, Hopf,
  spinor, chirality, and incidence data.
  test whether the hybrid preserves more required data than any single
  candidate without becoming unconstrained.
```

Existing related surfaces:

```text
sim_jax_native_geometry_g2_structure_probe.py
sim_jax_native_geometry_spin7_structure_probe.py
sim_jax_native_geometry_su3_calabi_yau_structure_probe.py
sim_jax_native_geometry_spin_c_structure_probe.py
sim_jax_native_geometry_symplectic_structure_probe.py
sim_jax_native_geometry_almost_complex_structure_probe.py
sim_g_structure_candidate_space_full_function_probe.py
sim_full_thirteen_layer_active_g_structure_both_chiral_source_native_composition_probe.py
```

## What Allows Stacking Later

Stacking is not allowed because two labels exist. It is allowed only after
independent parent maps have receipts and the composition order is tested.

For two admitted finite maps A and B:

```text
A : X -> Y
B : Y -> Z
```

Composition exists only when codomain(A) matches domain(B):

```text
B o A : X -> Z
```

Noncommutation test:

```text
OrderGap(A,B;x) =
  || B(A(x)) - A(B(x)) ||
```

If domains differ, define explicit adapters:

```text
Adapter_AB : codomain(A) -> domain(B)
Adapter_BA : codomain(B) -> domain(A)
```

and test:

```text
B(Adapter_AB(A(x))) vs A(Adapter_BA(B(x)))
```

Stacking controls:

```text
drop A
drop B
swap order
erase adapter metadata
replace both maps with commuting projections
erase shell/Hopf/chirality provenance
```

No stacking claim should start until the independent layer or geometry maps
listed above have current result receipts and the controls are named.

## Sim Standard For Each Individual Layer Or Geometry

A useful sim must emit a receipt with:

```text
classification
finite map
domain
codomain
carrier: source spinor network plus MPS/PEPS2D/PEPS3D view or justified reason
native scale variables, not unlabeled numbers
dynamic step or explicit reason the sim is invariant-only
entropy/QIT readouts when finite cuts exist
negative controls
load-bearing tool manifest
downstream locked consumers
result path
```

Minimum dynamic criteria:

```text
states evolve
connections or transports evolve when used
edge/cut weights evolve when claimed
shell possibility weights evolve when shell model is used
readouts change because the object changed, not because labels changed
```

Tool role criteria:

```text
torch or jax:
  numeric state evolution and gradients/parity where appropriate.

quimb/cotengra/opt_einsum:
  actual MPS/PEPS2D/PEPS3D carrier contractions or explicit blocked reason.

PyG/rustworkx/XGI/TopoNetX/GUDHI:
  finite graph/hypergraph/cell/topology checks when graph/cell claims are made.

sympy/z3/cvc5:
  symbolic or SMT checks for finite identities, impossibility gates, and
  hard negative controls.

clifford/e3nn/geomstats/JAX geometry tools:
  only load-bearing when their mathematical surface is actually invoked.
```

## Practical Execution Order Without New Row Codes

Run these as independent sims first:

```text
finite response quotient layer
source-native spinor network layer
literal shell possibility field layer
Hopf/projective/nested-torus transport layer
Clifford/quaternion/spin/twistor local structure layer
left/right Weyl sheet cover layer
each of the eight local Weyl dynamical-law candidates
each of the sixteen path placements, using explicit law and path formulas
local operator/channel action families
patch/gluing/groupoid compatibility layer
each separate geometry object listed above
each G-structure candidate listed above
entropy/QIT readouts across every layer and geometry where finite cuts exist
```

Only after those exist as current independent sims:

```text
pairwise layer order tests
pairwise geometry support tests
candidate G-structure preservation over layer stack
shell-to-Xi bridge tests
Phi0 candidate bakeoffs
flux derived-current tests
FEP/Holodeck finite process updates
physics/gravity interpretations
```

The target is not to make labels pass. The target is to make finite dynamic
maps over spinor-network geometry survive controls, then let the surviving
maps determine which layer order, geometry support, and readouts are real.
