# Full Manifold, Engine, Terrain, And Constraint Layout Draft

Status: bounded draft layout, not final manifold admission.

Created: 2026-05-25

## Authority And Boundary

This document lays out the current working manifold down to engine stage,
terrain, and operator substage grain. It separates source-backed runtime grammar
from candidate geometry that still has to be tested.

Main authority surfaces used:

- `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `system_v5/READ ONLY Reference Docs/terrains.md`
- `system_v5/READ ONLY Reference Docs/terrain math.md`
- `system_v5/ops/formal_scouts/canonical_qit_engine_specs.py`
- `system_v5/ops/formal_scouts/sim_constraint_manifold_foundation_alignment_gate_probe.py`
- `system_v5/ops/formal_scouts/sim_explicit_spinor_full_igt_64_substage_engine_cycle_probe.py`
- `system_v5/ops/formal_scouts/README.md`

The foundation gate currently says:

- `foundation_closed=false`
- `flux_layer_allowed=false`
- `downstream_axis0_allowed=false`

So the map below is a control surface for building and testing the manifold. It
is not a claim that the final geometry, final layer order, flux layer, Axis0,
Xi/Phi0 bridge, basin, physics, or PEPS3D closure has been admitted.

## Root Constraints

Everything starts from two root constraints:

| Root | Working meaning | Direct consequence |
|---|---|---|
| `F01_finitude` | finite distinguishable carrier, finite probes, finite histories, finite receiptable witnesses | no continuum-only or infinite-resolution geometry can be primitive |
| `N01_noncommutation` | order-sensitive operations, noncommuting probes, path/precedence dependence | static scalar readouts, commutative summaries, and unordered collapse are not enough |

The manifold should be read as nested or simultaneous constraint surfaces on a
state space, not a guaranteed linear ladder. A higher layer restricts the
admissible states and histories further; it does not erase lower constraints.

## Source-Backed Carrier Geometry

Current lower carrier grammar:

| Level | Object | Current status | Main test pressure |
|---|---|---|---|
| finite carrier/probe set | finite candidate states, finite effects, finite tests | partially supported | prove the probe family distinguishes the claimed states without hidden Cartesian/Pauli assumptions |
| complex Hilbert carrier | finite complex vectors and density operators | working carrier | do not let density matrices become primitive before carrier admission |
| unit spinor sheet | `psi in S^3 subset C^2` | source-backed chart | preserve explicit spinor/Hopf geometry |
| Hopf projection | `S^3 -> S^2` density/base readout | source-backed chart | keep projection/readout separate from carrier |
| Hopf torus leaf | fixed-eta torus `T_eta` with fiber and base-lift loops | source-backed chart | test inner/outer loop visibility separately |
| left/right Weyl sheets | Type 1 left with `H_L=+H0`, Type 2 right with `H_R=-H0` | source-backed chart | opposite Hamiltonian signs and ladder directions must survive controls |

Loop fields from the reference math:

| Loop | Runtime reading | Density visibility |
|---|---|---|
| inner / fiber loop | phase/fiber motion on the Hopf torus | density is mostly gauge-hidden and should not be overread |
| outer / base-lift loop | horizontal/base motion on the Hopf torus | density changes through base motion |

## Terrain Families

There are four perception/topology families and eight chiral terrain
realizations:

| Family | Type 1 / left terrain | Type 2 / right terrain |
|---|---|---|
| `Se` | Funnel | Cannon |
| `Ne` | Vortex | Spiral |
| `Ni` | Pit | Source |
| `Si` | Hill | Citadel |

Terrain-law roles:

| Terrain | Sheet | Core role |
|---|---|---|
| Funnel | Type 1 left | dephasing/projection sink-like terrain |
| Vortex | Type 1 left | circulation / Hamiltonian plus dissipative perturbation |
| Pit | Type 1 left | lowering dissipator / absorbing basin |
| Hill | Type 1 left | stabilized plateau / projector dephasing |
| Cannon | Type 2 right | release/source projection |
| Spiral | Type 2 right | reverse circulation / outward projection |
| Source | Type 2 right | raising dissipator / emitting basin |
| Citadel | Type 2 right | protected plateau / projector dephasing |

## Engine Stage Grammar

The current operational engine grammar is:

- two engine types;
- eight macro stages per engine;
- four operator substages per macro stage;
- thirty-two substages per engine;
- sixty-four substages across the paired Type 1 + Type 2 cycle;
- each macro stage has one perception/topology and one loop class;
- all four operator substages inherit the macro-stage Axis6 sign.

Current schedule in `canonical_qit_engine_specs.py`:

| Engine | Macro-stage order |
|---|---|
| Type 1 / left Weyl | `Se outer`, `Ne outer`, `Ni outer`, `Si outer`, `Se inner`, `Si inner`, `Ni inner`, `Ne inner` |
| Type 2 / right Weyl | `Se outer`, `Si outer`, `Ni outer`, `Ne outer`, `Se inner`, `Ne inner`, `Ni inner`, `Si inner` |

The full placement inventory remains the 16 sheet-loop-terrain placements:

| # | Placement |
|---:|---|
| 1 | Type 1 inner Funnel / `Se` |
| 2 | Type 1 inner Vortex / `Ne` |
| 3 | Type 1 inner Pit / `Ni` |
| 4 | Type 1 inner Hill / `Si` |
| 5 | Type 1 outer Funnel / `Se` |
| 6 | Type 1 outer Vortex / `Ne` |
| 7 | Type 1 outer Pit / `Ni` |
| 8 | Type 1 outer Hill / `Si` |
| 9 | Type 2 inner Cannon / `Se` |
| 10 | Type 2 inner Spiral / `Ne` |
| 11 | Type 2 inner Source / `Ni` |
| 12 | Type 2 inner Citadel / `Si` |
| 13 | Type 2 outer Cannon / `Se` |
| 14 | Type 2 outer Spiral / `Ne` |
| 15 | Type 2 outer Source / `Ni` |
| 16 | Type 2 outer Citadel / `Si` |

## Topology, Loop, Operator, Sign Table

The canonical topology table gives the chart-locked loop operators and signs.
The four operator substages then run the full slot sequence
`Ti`, `Te`, `Fi`, `Fe` under the macro-stage sign.

Type 1 / left Weyl:

| Topology | Terrain | Pattern | Outer op/sign/result | Inner op/sign/result | Axis | Rate | Mode |
|---|---|---|---|---|---|---:|---|
| `Se` | Funnel | `LOSEwin` | `Ti + result=LOSE` | `Fi - result=win` | x | 0.18 | sink_capture |
| `Ne` | Vortex | `WINlose` | `Ti - result=WIN` | `Fi + result=lose` | y | 0.13 | circulation |
| `Ni` | Pit | `loseLOSE` | `Fe - result=LOSE` | `Te + result=lose` | z | 0.28 | absorbing_basin |
| `Si` | Hill | `winWIN` | `Fe + result=WIN` | `Te - result=win` | z | 0.20 | stabilized_plateau |

Type 2 / right Weyl:

| Topology | Terrain | Pattern | Outer op/sign/result | Inner op/sign/result | Axis | Rate | Mode |
|---|---|---|---|---|---|---:|---|
| `Se` | Cannon | `loseWIN` | `Fi + result=WIN` | `Ti - result=lose` | x | 0.18 | source_projection |
| `Ne` | Spiral | `winLOSE` | `Fi - result=LOSE` | `Ti + result=win` | y | 0.15 | reverse_circulation |
| `Ni` | Source | `LOSElose` | `Te - result=LOSE` | `Fe + result=lose` | x | 0.27 | emitting_basin |
| `Si` | Citadel | `WINwin` | `Te + result=WIN` | `Fe - result=win` | z | 0.21 | protected_plateau |

Canonical operator generators:

| Operator | Generator | Family |
|---|---|---|
| `Ti` | `sigma_z` | z pinching/dephase |
| `Te` | `sigma_x` | x pinching/dephase |
| `Fi` | `sigma_x` | x coherent rotation |
| `Fe` | `sigma_y` | antisymmetric coherent rotation |

Source-conformance issue to repair before using the 64-substage scout as a
full dynamics proof: `canonical_qit_engine_specs.py` maps `Fe` to `sigma_y`,
but `sim_explicit_spinor_full_igt_64_substage_engine_cycle_probe.py` currently
applies `Fe` as `sigma_z` in its local `operator_matrix`. Until fixed, that
scout can support row-count/stage grammar only, not final `Fe` dynamics.

## Ordered Tokens And Precedence

The ordered token layer is not optional. These tokens preserve operator-vs-
terrain precedence and Axis6 sign:

| Topology family | Native ordered tokens |
|---|---|
| `Se` | `TiSe`, `SeTi`, `FiSe`, `SeFi` |
| `Ne` | `TiNe`, `NeTi`, `FiNe`, `NeFi` |
| `Ni` | `FeNi`, `NiFe`, `TeNi`, `NiTe` |
| `Si` | `FeSi`, `SiFe`, `TeSi`, `SiTe` |

Any runtime that drops chart-locked tokens such as `NiTe` or `SiTe`, drops
Axis5/Axis6 role information, or collapses precedence into unordered topology
labels is not source-conformant for engine promotion.

## Candidate Manifold Layer Stack

The 13-layer stack below is an operational fixture vocabulary. It is useful for
planning and tests, but the repo explicitly does not treat the exact count,
linear order, or topology as root-derived canon.

| Candidate layer | Name | Constraint role | What has to be tested |
|---:|---|---|---|
| 0 | `finite_constraint_complex` | finite admissible candidates and probes | effect algebra laws, finite distinguishability, root-only controls |
| 1 | `complex_hilbert_carrier` | complex carrier for amplitudes/densities | whether Hilbert structure is forced or only a working carrier |
| 2 | `unit_spinor_sphere` | unit spinor `S^3` sheet | spinor/quaternion equivalence and gauge handling |
| 3 | `projective_base_sphere` | Hopf base / density-visible readout | projection controls and density-adapter demotion tests |
| 4 | `hopf_fiber_bundle` | fiber/base separation | inner loop gauge-hidden vs outer loop visible density |
| 5 | `hopf_torus_leaf_family` | nested torus leaves | which eta leaves and loop pairs preserve terrain distinctions |
| 6 | `connection_holonomy_geometry` | ordered transport / holonomy | noncommuting loop order, horizontal lift, holonomy controls |
| 7 | `weyl_spinor_bundle` | left/right chiral sheets | Hamiltonian sign, ladder direction, sheet-exchange controls |
| 8 | `chirality_orientation_cover` | orientation/chirality cover | whether chirality survives controls beyond label swapping |
| 9 | `clifford_module_geometry` | Clifford action / rotor transport | Clifford generators as tools, not primitive substrate claims |
| 10 | `frame_bundle_structure_reduction` | reduced frame/G-structure candidates | survivor quotient and special-form controls |
| 11 | `tensor_product_coupling_geometry` | MPS/PEPS/PEPS3D-like coupling carriers | full environment closure, not local/sampled substitute |
| 12 | `dynamic_transition_ratchet_geometry` | transition, hysteresis, basin/ratchet candidate | long-horizon countermodels, basin falsifiers, blocked final convergence |

This stack should be tested as a partial order or DAG, not only as a chain.
Some layers may activate together; some orders may fail; some layer names may
split or collapse under discriminator tests.

## Highest Constraint Surface Currently In Scope

The highest currently expressible manifold constraint is not Axis0. It is the
candidate dynamic transition/ratchet layer over a corrected spinor/Hopf/Weyl
and tensor-coupled carrier, with flux only as a derived manifold layer after
lower closure.

Current required order:

1. Close lower finite-effect and Weyl/spinor carrier gaps.
2. Remove or explicitly demote density-adapter crutches where they carry the
   claim.
3. Repair source-conformant 64-substage engine runtime, including `Fe`.
4. Prove tensor carrier portability without dense/local-only shortcuts.
5. Establish PEPS/PEPS3D environment closure or record the exact blocker.
6. Build flux as a layer over the corrected lower manifold.
7. Only then allow downstream Axis0 readouts over admitted flux/history.
8. Only after that revisit Xi/Phi0, basin, physics, gravity, or bridge claims.

Current blocked upper claims:

| Surface | Current status |
|---|---|
| flux layer | blocked until lower manifold layers are correct |
| Axis0 | downstream only; not primary science lane |
| PEPS3D closure | local/sampled stress is not full environment closure |
| Xi/Phi0 bridge | candidate/falsifier lane only |
| attractor-basin convergence | not admitted; finite fixture and long-horizon falsifiers block real convergence |
| physics/gravity/Standard Model | out of scope until lower proof chain changes |

## Test Program

The next admissible work is not "make one big manifold sim." It is a layer and
handoff discriminator grid.

Minimum tests by layer:

| Test gate | Positive requirement | Negative/control requirement |
|---|---|---|
| finite effect/probe gate | finite states are separated by finite probes | collapse to scalar/readout-only fails |
| Hopf loop gate | inner and outer loops have the expected visibility distinction | hiding the loop erases the distinction |
| sheet gate | left/right Weyl signs and ladder directions separate | swapped Hamiltonian or swapped ladder fails |
| terrain gate | all eight terrains produce distinct controlled roles | one-terrain-only and terrain-erased controls fail |
| operator-token gate | ordered tokens and Axis6 signs are load-bearing | unordered token collapse and mixed sign within macro stage fail |
| engine-cycle gate | 2 engines x 8 stages x 4 operators = 64 substages | 32-row, native-only, or one-engine collapse fails |
| layer-order gate | candidate layers survive local nesting and composition tests | wrong order, omitted parent, and shortcut carrier controls fail |
| tensor-carrier gate | MPS/PEPS/PEPS3D portability keeps readouts without dense shortcuts | dense, local-only, and sampled-only substitutes are demoted |
| flux gate | flux is derived from corrected lower manifold dependencies | sheet-erased, shell-erased, topology-frozen, and scalar-only controls fail |
| Axis0 gate | Axis0 reads admitted flux/history without becoming primitive | Axis0-only and unsigned scalar controls fail |
| basin gate | convergence survives perturbation, horizon, and carrier controls | finite fixture and long-horizon countermodels must be absent or classified |

## Working Shape

The manifold to test is:

```text
F01/N01 roots
  -> finite effect/probe carrier
  -> complex/spinor carrier
  -> Hopf projection and Hopf torus loops
  -> left/right Weyl chiral sheets
  -> eight terrain generators
  -> 16 terrain-loop placements
  -> 64 operator substages across paired engines
  -> candidate layer stack / partial-order constraint tests
  -> tensor-coupled carrier tests
  -> derived flux layer
  -> downstream Axis0 readout
  -> Xi/Phi0 and basin candidates only after admission gates change
```

The live open problem is to discover which of the candidate layers are real
constraint surfaces, which are chart/readout artifacts, and which composition
orders survive. The system should therefore test local geometry choices and
composition orders instead of freezing a final layer order now.
