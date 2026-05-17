# Axis Terrain Manifold Correction Handoff

Status: working handoff, not canon.

Purpose: preserve the recent correction that the main build target is the
geometric constraint manifold that generates/supports the two Weyl operating
spaces and their terrain vector fields. This note exists so future sim work
does not drift back into downstream gamma5, boundary, shell, persistence, or
entropy readouts before the source object is mature enough.

## Core Correction

The recent formal-scout loop went off track because it tested downstream
readouts before the actual source object was built strongly enough.

The missing source object is:

```text
geometric constraint manifold
-> left/right Weyl spinor sheets plus flux orientation
-> 8 terrain generator families
-> valid constrained four-stage cycles
-> only then entropy/coherent-information/boundary/shell readouts
```

Downstream readouts are useful only after they consume real source-native
histories from the manifold. They cannot stand in for the manifold.

## Geometry Before Axes

Axes are not the primitive substrate. They are readout or control maps over the
constraint manifold:

```text
A_i : M(C) -> V_i
```

The geometric constraint layer must be kept distinct from axis overlays.

Current separation:

```text
left/right Weyl spinor = geometric constraint layer
in/out flux = geometric constraint layer
yin-yang mirror flip = possible outside-axis transform
axes = maps/control/readouts on the built space
```

Do not force the left/right Weyl split or flux split into Axis 3 unless a
separate sim proves that collapse.

## Axis Overlay Corrections

These are overlay handles, not executable objects.

```text
Axis 0 = positive feedback loop vs negative feedback loop
```

Axis 0 is not hot/cold and not hotter/colder. It is feedback sign from
deviation:

```text
deviation = state - reference/attractor/constraint target
positive feedback = amplifies deviation / raises variance
negative feedback = suppresses deviation / lowers variance
```

A negative-feedback loop can stabilize hot or cold. A positive-feedback loop
can run toward hotter or colder. Temperature level and heat-flow comparison
belong elsewhere.

```text
Axis 1 and Axis 2 = the two binary coordinates that generate the four
terrain/topology stage classes
```

Axis 1 and Axis 2 form the stage/topology edge basis:

```text
Axis 1 x Axis 2 = Se, Ne, Ni, Si
```

Axis 0 cannot be swapped into an Axis 1/2 slot. If it is, the graph edges are
not valid engine-cycle stages.

```text
Axis 4 = heat-flow / ordering direction
```

Thermodynamic overlay:

```text
hotter vs colder
entropy sent outward vs inward
deductive vs inductive
```

Math kernel:

```text
Phi_D = exp(t_R L_R) exp(t_C L_C)
Phi_I = exp(t_C L_C) exp(t_R L_R)
Phi_D - Phi_I approx t_R t_C [L_R, L_C]
```

```text
Axis 5 = heat level / excitation intensity
```

Thermodynamic overlay:

```text
hot vs cold
```

Math kernel:

```text
gradient / Lindblad / semigroup generator class
vs
spectral / Hamiltonian / group generator class
```

```text
Axis 6 = action orientation
```

Overlay:

```text
up vs down
judging-first vs perceiving-first
```

Math kernel:

```text
L_A(rho) = A rho
R_A(rho) = rho A
```

## Thermodynamic 2x2 Terrain Candidate

The four thermodynamic stage classes are:

```text
adiabatic open
isothermal open
adiabatic closed
isothermal closed
```

Current candidate mapping:

| Topology | Thermodynamic class |
|---|---|
| `Se` | isothermal open |
| `Ne` | isothermal closed |
| `Ni` | adiabatic open |
| `Si` | adiabatic closed |

This mapping is a candidate and must be tested against the terrain generator
laws and actual cyclic work production. It should not be treated as already
proved by label agreement.

## Valid Four-Stage Cycles

The valid terrain-stage loop orders are constrained. Do not treat arbitrary
permutations as valid engine cycles.

Current valid cycle pair:

```text
Si -> Se -> Ne -> Ni
Si -> Ni -> Ne -> Se
```

Candidate overlay:

```text
deductive = Si -> Se -> Ne -> Ni
inductive = Si -> Ni -> Ne -> Se
```

These cycles should be tested as constrained graph cycles that run and do work.
Carnot and Szilard are optional independent calibration baselines only. They are
not dependencies for building the QIT engines.

## Eight Terrains On Weyl Sheets

There are eight terrain names because there are four terrain generator families
on the left Weyl sheet and four mirrored/different families on the right Weyl
sheet.

| Topology | Thermodynamic candidate | Left Weyl terrain | Right Weyl terrain |
|---|---|---|---|
| `Se` | isothermal open | Funnel | Cannon |
| `Ne` | isothermal closed | Vortex | Spiral |
| `Ni` | adiabatic open | Pit | Source |
| `Si` | adiabatic closed | Hill | Citadel |

These names must map to actual math. The useful object is not the name, and not
mainly inner/outer loop placement. It is the terrain generator/vector field on
Weyl density states.

For Weyl densities:

```math
rho_L = psi_L psi_L^\dagger = 1/2(I + r_L . sigma)
rho_R = psi_R psi_R^\dagger = 1/2(I + r_R . sigma)
H_L = +H_0
H_R = -H_0
```

The eight terrain generator families are:

```math
Funnel:
X_F^L(rho_L) =
sum_k D[L_k^{F,L}](rho_L) - i eps_{F,L}[H_L,rho_L]
```

```math
Vortex:
X_V^L(rho_L) =
-i[H_L,rho_L] + eps_{V,L} sum_k D[M_k^{V,L}](rho_L)
```

```math
Pit:
X_P^L(rho_L) =
gamma_{P,L} D[sigma_-](rho_L) - i eps_{P,L}[H_L,rho_L]
```

```math
Hill:
X_H^L(rho_L) =
-i[K_L,rho_L]
+ sum_j kappa_{H,L,j}
  (P_j rho_L P_j - 1/2(P_j rho_L + rho_L P_j))
```

```math
Cannon:
X_C^R(rho_R) =
sum_k D[L_k^{C,R}](rho_R) - i eps_{C,R}[H_R,rho_R]
```

```math
Spiral:
X_S^R(rho_R) =
-i[H_R,rho_R] + eps_{S,R} sum_k D[M_k^{S,R}](rho_R)
```

```math
Source:
X_{So}^R(rho_R) =
gamma_{So,R} D[sigma_+](rho_R) - i eps_{So,R}[H_R,rho_R]
```

```math
Citadel:
X_{Ci}^R(rho_R) =
-i[K_R,rho_R]
+ sum_j kappa_{Ci,R,j}
  (P_j rho_R P_j - 1/2(P_j rho_R + rho_R P_j))
```

with:

```math
D[A](rho) = A rho A^\dagger
- 1/2(A^\dagger A rho + rho A^\dagger A)
```

## What Has Been Simed

Minimal v5 repair scout:

```text
system_v5/ops/formal_scouts/
sim_left_right_weyl_density_terrain_loop_placement_mirror_non_equivalence_probe.py
```

It minimally instantiates:

```text
rho_L / rho_R
H_L = +H_0 / H_R = -H_0
sigma_- vs sigma_+
8 terrain generator families as finite fixtures
16 terrain-loop placements
left/right mirror non-equivalence
```

Reported result:

```text
16 placements executed
16 distinct finite readout signatures
min left/right mirror gap about 0.231
validator passed
```

This is not enough to claim the manifold is mature. It only shows a finite
fixture can run.

## What Has Not Been Simed Enough

The constraint manifold has not yet been maturely simed to support the terrain
families as a strong claim.

Open gaps:

```text
1. why these 8 generator families are forced by the constraint manifold
2. how Weyl sheets, flux, and terrain laws emerge from nested geometry
3. how the four terrain classes map cleanly to thermodynamic stages
4. why only the two valid cycles are admissible
5. whether the cycles produce real work as engines
6. whether entropy/coherent-information readouts survive after the source object is built
7. whether the structure scales beyond tiny finite fixtures
```

## Corrected Main Focus

The next main build target should be:

```text
constraint manifold
-> Weyl sheets plus flux
-> 8 terrain generator families
-> two valid four-stage cycles
-> actual cyclic work production
-> QIT/nonclassical entropy and coherent-information readouts
```

Not:

```text
gamma5 channel readout
boundary projection
shell graph persistence
Choi distance
coherent information
```

Those are downstream tools. They become meaningful after the source-native
terrain histories exist.

## Next Sim Requirements

The next sims should not merely instantiate the 8 terrains by hand. They should
test whether the manifold supports them.

Minimum next scout family:

```text
geometric constraint manifold -> Weyl sheets + in/out flux -> terrain generator families
```

Required negatives:

```text
wrong nesting order
no Weyl sheet split
flux erased
same flux on both sheets
Hamiltonian sign erased
sigma_- / sigma_+ erased
terrain family merged
arbitrary permutation of stage order
invalid four-stage loop
wrong-order cyclic-work controls
```

Claim ceiling must stay:

```text
formal_scout
promotion_allowed: false
```

until the manifold generates or strongly constrains the terrain families rather
than merely hosting hand-assigned generator fixtures.

## Carnot And Szilard Boundary

Carnot and Szilard cycles are not the main target.

They are independent baseline engines that can be simulated to prove that this
repo can build and audit cycle mechanics at all. They may help teach the bridge
from classical engine mechanics to QIT engine mechanics, but they are not a gate
on the QIT terrain engines.

The main target is actual cyclic QIT engines:

```text
state moves around a constrained cycle
the cycle changes the state or environment
the cycle produces measurable work/useful transformation
the cycle has wrong-order and no-work controls
```

The desired endpoint is not a labeled placement table. It is engines that run.
The QIT engines may be especially useful if their cyclic work is connected to
neural-network or tensor-network computation, where the terrain cycles act as
trainable/nonclassical update loops rather than inert symbolic stages.
