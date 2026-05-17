# Left And Right Chiral Operating Space Build Note

Status: source-grounded noncanonical build target for formal scouts.

This is not new information. It is a restatement of an existing core build
requirement so the current v5 scout work does not drift away from the main
two-chiral-operating-space construction.

Source surfaces read for this note:

- `system_v5/docs/ENGINE_MATH_REFERENCE.md`
- `system_v5/READ ONLY Reference Docs/terrains.md`
- `system_v5/READ ONLY Reference Docs/Formal constraints and geometry .md`
- `READ ONLY Legacy core_docs/QIT_GRAPH_LAYER_MAPPING.md`
- `READ ONLY Legacy core_docs/QIT_GRAPH_RUNTIME_MODEL.md`

## Purpose

The immediate build object remains two executable chiral operating spaces:

- left chiral operating space
- right chiral operating space

Source language often names these Type 1 and Type 2, but new v5 scout names
should use literal math names. These are not a new idea and not a side finding:
they are the existing left/right Weyl sheet engine families.

They are mirrored in construction but must not be collapsed into one object with
a sign flag. The point is to give the independent degrees of freedom a runnable
space, then test whether each space can run complete finite loops.

This is not a physics proof target. Physics readings such as matter/antimatter
asymmetry stay downstream until the operating spaces exist as runnable math.

## Required Structure

The source-grounded carrier is:

`\psi_L, \psi_R in C^2, ||psi||=1`

`\rho_L = psi_L psi_L^\dagger = 1/2(I + r_L . sigma)`

`\rho_R = psi_R psi_R^\dagger = 1/2(I + r_R . sigma)`

`H_L = +H_0`, `H_R = -H_0`.

The left/right Bloch laws are:

`\dot r_L = 2 n x r_L`

`\dot r_R = -2 n x r_R`.

The Hopf-torus loop placements are:

- left fiber loop: `Gamma_f^L`
- left base-lift loop: `Gamma_b^L`
- right fiber loop: `Gamma_f^R`
- right base-lift loop: `Gamma_b^R`

The source-grounded count is:

- 4 terrain law families per chiral space;
- 2 loop placements per chiral space;
- 8 placements per chiral space;
- 16 placements total.

The graph mapping separately states that each engine family has an 8-stage
cycle and 4-operator subcycle grain. That means a scout must not confuse:

- terrain law family;
- inner/fiber versus outer/base-lift placement;
- inductive versus deductive traversal order;
- operator subcycle order;
- left/right Weyl family.

The two spaces should be tested as independent engine families. A valid scout
must show both that they can run the same class of loop and that they do not
reduce to one another under the allowed controls.

## Source-Grounded Terrain Laws

Left chiral operating space:

- `Se`: `X_F^L(rho_L) = sum_k D[L_k^{F,L}](rho_L) - i eps_{F,L}[H_L,rho_L]`
- `Ne`: `X_V^L(rho_L) = -i[H_L,rho_L] + eps_{V,L} sum_k D[M_k^{V,L}](rho_L)`
- `Ni`: `X_P^L(rho_L) = gamma_{P,L} D[sigma_-](rho_L) - i eps_{P,L}[H_L,rho_L]`
- `Si`: `X_H^L(rho_L) = -i[K_L,rho_L] + sum_j kappa_{H,L,j}(P_j rho_L P_j - 1/2(P_j rho_L + rho_L P_j))`

Right chiral operating space:

- `Se`: `X_C^R(rho_R) = sum_k D[L_k^{C,R}](rho_R) - i eps_{C,R}[H_R,rho_R]`
- `Ne`: `X_S^R(rho_R) = -i[H_R,rho_R] + eps_{S,R} sum_k D[M_k^{S,R}](rho_R)`
- `Ni`: `X_So^R(rho_R) = gamma_{So,R} D[sigma_+](rho_R) - i eps_{So,R}[H_R,rho_R]`
- `Si`: `X_Ci^R(rho_R) = -i[K_R,rho_R] + sum_j kappa_{Ci,R,j}(P_j rho_R P_j - 1/2(P_j rho_R + rho_R P_j))`

The load-bearing pair differences are:

- `H_L = +H_0` versus `H_R = -H_0`;
- `sigma_-` sink law versus `sigma_+` source law;
- distinct left and right dissipative families;
- distinct retained-strata projectors;
- distinct loop ownership on `Gamma_f` and `Gamma_b`.

## Minimal Math Surface

Use pure math names in code and receipts:

- `left_chiral_operating_space`
- `right_chiral_operating_space`
- `left_weyl_density`
- `right_weyl_density`
- `fiber_loop`
- `base_lift_loop`
- `terrain_law`
- `terrain_loop_placement`
- `eight_stage_loop`
- `inductive_traversal`
- `deductive_traversal`
- `mirror_involution`
- `gamma5_projector`
- `density_channel`
- `coherent_information`
- `conditional_entropy`
- `offdiagonal_chirality_coherence`

Avoid labels that hide the object being simulated. The sim name should say what
math is being run.

## First Formal Scout Shape

Recommended first scout name:

`sim_left_right_weyl_density_terrain_loop_placement_mirror_non_equivalence_probe.py`

Math object:

Two finite density-channel placement systems:

`(rho_L, Gamma_f^L/Gamma_b^L, X_F^L/X_V^L/X_P^L/X_H^L)`

`(rho_R, Gamma_f^R/Gamma_b^R, X_C^R/X_S^R/X_So^R/X_Ci^R)`

with a mirror involution `M` that maps left/right sheet, Hamiltonian sign, and
ladder direction. The scout checks whether corresponding left/right placements
remain distinguishable under finite density readouts after matching traversal
orders.

Positive predicates:

- every left terrain law emits valid density states;
- every right terrain law emits valid density states;
- all four left loop placements execute;
- all four right loop placements execute;
- inner/fiber density-stationary behavior differs from outer/base-lift density-traversing behavior;
- mirror involution maps `H_L` to `H_R` and `sigma_-` to `sigma_+`;
- at least one readout separates the mirrored left/right placement pairs;
- inductive and deductive traversal orders both execute over the same placement set.

Graveyard controls:

- identical left/right rates;
- wrong Hamiltonian sign;
- swapped ladder operator;
- loop placement hidden;
- one terrain law only;
- shuffled traversal order;
- symmetric effective channel fit;
- arbitrary same-channel control;
- projection that erases left/right offdiagonal coherence.

Claim ceiling:

Formal scout only. It can show that the two chiral operating spaces are runnable
and distinguishable under finite probes. It cannot claim psychology, physics,
matter/antimatter explanation, or final engine identity.

## Design Rule

Do not let boundary or constraint maps erase the object being built. A map that
commutes with gamma5 may still destroy the offdiagonal chirality coherence that
makes the two operating spaces distinguishable. Long-horizon tests must report
whether the chiral separation survives, decays, or only exists transiently.
