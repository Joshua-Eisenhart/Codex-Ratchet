# Geometry Vs G-Structure And Layer Completion Correction - 2026-05-28

Status: correction artifact for the current layer/geometry formal-scout lane.
This is not a sim result, not a G-structure selection, not a layer completion
receipt, not stacking, not flux, not Xi/Phi0, not Axis0, not FEP/Holodeck, not
physics/gravity, and not final manifold admission.

## Correction

The current 12 rows previously described as `G-structure candidates` are not
the true G-structures.

They are standalone geometry, carrier, fibration, bundle, spinor, Hopf,
twistor, Clifford, and reduction-graph scout receipts. They are separate things
to sim. They can be inputs to later G-structure selection or synthesis, but they
are not themselves completed G-structures.

The current layer truth is also stricter:

```text
fully complete layer rows: 0
true G-structure rows completed: 0
official G-structure selected: false
layer embedding into selected G-structure: false
layer stacking/order testing: blocked
final manifold admission: false
```

## What Exists

The current status file:

```text
system_v5/ops/formal_scouts/layer_g_structure_entropy_individual_sim_status_20260528.json
```

records useful bounded scout coverage:

```text
9 layer rows have per-layer scout receipts
12 standalone geometry-scout rows have receipts
39 result receipts are present in the current status surface
8/16/32/64 scale appears in the status surface
MPS/PEPS2D/PEPS3D views appear in the status surface
QIT entropy/readouts are derived readouts
blocked consumers remain blocked
```

That is not the same as a fully completed layer or a completed G-structure.

## Correct Categories

### Layer Rows

Layer rows are the L0-L8 manifold-layer candidates:

```text
L0 response/effect/path quotient
L1 boundary/environment/closure
L2 Weyl spinor/chirality
L3 Clifford/quaternion invariant
L4 terrain/channel/generator
L5 operator substage
L6 entropy/cut/communication
L7 Hopf/fibration/shell projection
L8 gluing/groupoid/equivariant/dynamic candidate
```

Current status:

```text
bounded formal-scout coverage
not full layer completion
not parent-complete for broad order/nesting tests
```

### Standalone Geometry Scouts

These are the 12 rows that were mislabeled as G-structures:

```text
S3_spinor_carrier
S2_Hopf_base_surface
Hopf_fibration_S3_to_S2
Nested_Hopf_tori
Clifford_torus_T2_in_S3
Twistor_incidence_spinor_geometry
U1_Hopf_principal_bundle
SU2_Spin3_unit_quaternion_double_cover
SO3_orientation_frame_reduction
Pin3_Spin3_chirality_split
Clifford_geometries_Cl3_Cl6
Hybrid_Hopf_Spin_Twistor_Clifford_reduction_graph
```

Current status:

```text
bounded standalone geometry/carrier/fibration scout coverage
not true G-structure completion
not official G-structure selection
not layer embedding
```

### True G-Structure Work

True G-structure work is a later task. It has to test whether some structure or
hybrid structure can carry the layer system without being invented on the fly.

A true G-structure candidate must declare:

```text
finite structure object
finite group / bundle / frame / reduction / connection data where applicable
how it acts on or constrains the layer carrier
how it preserves spinor phase, chirality, shell orientation, and PEPS3D locality
which standalone geometry scouts it uses or rejects
which layer rows it can carry
which layer rows it cannot carry
negative controls
tool ablations
blocked consumers
```

No current receipt satisfies that full role.

## Correct Next Work

Do not start broad order tests or nested-layer result comparisons yet.

The next work must be one of:

```text
1. finish/deepen one individual L0-L8 layer until it becomes parent-complete;
2. lift one root-adjacent geometry alternative into a full standalone geometry scout;
3. build a true G-structure candidate test that consumes existing geometry scouts;
4. write a parent-completion table proving which rows are complete enough for
   intrinsic order tests and which remain incomplete.
```

The current gate for any order/nesting work is:

```text
system_v5/ops/NONCOMMUTATION_AND_NESTED_LAYER_TEST_GATE_20260528.md
```

That gate blocks broad order/nesting tests until parent rows are actually
complete under the current extended standard.

