# Noncommutation And Nested Layer Test Gate - 2026-05-28

Status: active sequencing gate for order tests and nested-layer comparisons.
This is not a result receipt, not stacking admission, not flux, not Xi/Phi0,
not Axis0, not FEP/Holodeck, not physics/gravity, and not final manifold
completion.

## Controlling Correction

Do not start broad noncommutation-order sweeps or nested-layer result
comparisons on partial, proxy, root-adjacent, adapter-only, or bounded-scout-only
rows.

Only test how noncommuting orders or nested layers produce different results
after the parent sims are complete under the current layer/G-structure standard.

The current standard is not "a row ran." A completed parent sim must satisfy:

```text
F01 finite carrier/probe/operator/path witness
N01 local noncommuting or order-sensitive witness/control
finite_map: domain -> codomain_or_output
torch-native spinor or spinor-derived density where applicable
PEPS3D K=(V,E,F,C) where claiming source-native geometry
MPS/PEPS2D/PEPS3D views where applicable
QIT entropy/readouts as derived outputs, not primary object
tool manifest and tool integration depth
non-vacuous tool ablation delta
8/16/32/64 stress or explicit resource blocker
negative controls
claim ceiling
blocked consumers
fresh local rerun
```

For shell, Axis0, FEP, gravity, or flux language, the parent sim must also
preserve:

```text
Sigma_r
i/r shell order
Omega_r
j/k future-fuzz indices
future-inward orientation
past-outward record
rho_Br
rho_IrBr
compatibility weights
compression into rho_present
outward record
readout provenance
```

## Important Distinction

N01 is still required inside each individual layer sim.

That local N01 check answers:

```text
does this individual layer have a real finite noncommuting/order-sensitive
operation or control?
```

The blocked work is different. Broad order testing answers:

```text
given a completed parent sim, do different admissible operation orders produce
different layer outputs?
```

Nested-layer testing answers:

```text
given two or more completed parent layer sims with compatible carriers, do
different nesting orders produce different outputs?
```

Those second and third questions must not run until the parent sims are complete.

## Current Repo Status

The current layer/G-structure status file reports strong bounded formal-scout
coverage:

```text
system_v5/ops/formal_scouts/layer_g_structure_entropy_individual_sim_status_20260528.json
```

It also says:

```text
claim_ceiling = bounded formal-scout coverage only
official_g_structure_selected = false
layer_embedding_admitted = false
blocked_consumers include layer_stacking and cross_layer_order_closure
```

Therefore, the current correct status is:

```text
individual layer and G-structure scout coverage: useful and bounded
broad noncommutation-order sweeps across these rows: not opened by status alone
nested-layer result comparison: still blocked until parent-completion gate passes
```

## Stage 0 - Parent Completion Audit

Before any order or nesting test, write or update a parent-completion table.

Each row must have:

```text
parent_id
source_sim
result_path
fresh_rerun_status
completion_status:
  incomplete
  complete_for_intrinsic_order_test
  complete_for_pairwise_nesting_test
  complete_for_multi_layer_nesting_test
missing_fields
blocked_consumers
```

Completion requires the actual result receipt. A controller summary is not
enough.

If no parent row reaches `complete_for_intrinsic_order_test`, stop. Continue
individual layer sim work instead.

## Stage 1 - Intrinsic Order Test On One Completed Parent

Run only after one parent row is complete.

Finite map shape:

```text
OrderTest_Li:
  (completed parent layer Li, finite admissible operation/path family O,
   order family pi in Perm(O), controls)
  -> output signatures, entropy/readout deltas, order gaps, controls, blockers
```

Allowed claim:

```text
this completed layer has order-sensitive output differences under these finite
admissible orders
```

Required controls:

```text
commuting operation family
order-erased operation labels
same inventory with shuffled labels only
product/no-entanglement carrier where relevant
scalar entropy primary rejected
dense closure rejected
PEPS3D label-only rejected
```

Stop condition:

```text
if the order gap survives commuting or order-erased controls, the test is
invalid and must be repaired before any nesting test
```

## Stage 2 - Pairwise Nested-Layer Test

Run only after both parent layers are complete and at least one relevant
intrinsic order test has passed for each parent.

Finite map shape:

```text
NestedPairTest_Li_Lj:
  (completed parent Li, completed parent Lj, common carrier projection P,
   admissible nesting orders [Li then Lj, Lj then Li], controls)
  -> paired output signatures, survivor sets, entropy/readout deltas,
     order gaps, failed controls, blockers
```

Required preflight:

```text
carrier compatibility:
  same PEPS3D K or explicit projection between carriers
spinor compatibility:
  spinor payloads or spinor-derived densities map without dense closure
readout compatibility:
  QIT readouts have shared cut/provenance
blocked consumers:
  stacking/flux/Xi/Phi0/Axis0/FEP/physics remain blocked unless explicitly opened
```

Allowed claim:

```text
for this completed pair and this finite common carrier/projection, nesting order
changes or does not change these measured outputs
```

No claim about final stacking, final layer order, flux, Axis0, FEP, gravity, or
the full manifold is allowed.

## Stage 3 - Small Nested Subset Test

Run only after pairwise nesting tests identify a compatible subset.

Finite map shape:

```text
NestedSubsetTest_S:
  (completed parent subset S, common carrier/projection, finite admissible order
   family Pi(S), controls)
  -> output signatures, survivor structures, entropy/readout deltas,
     pairwise-residual agreement, blockers
```

Required controls:

```text
one parent removed
one parent replaced by adapter-only proxy
carrier projection erased
order family commuted
shell orientation erased if shell language appears
QIT readout-only proxy
```

Stop condition:

```text
if a proxy/adaptor-only row can replace a completed parent without loss, the
subset test is invalid as manifold evidence
```

## Stage 4 - Candidate Stack Test

Run only after enough pairwise and subset tests pass to name a specific candidate
stack.

Finite map shape:

```text
CandidateStackTest:
  (completed parents L*, selected G-structure or explicit no-selection blocker,
   common PEPS3D carrier/projection, finite nesting order family, controls)
  -> stack output signatures, survivor geometry, readout deltas,
     order-dependence map, unresolved blockers
```

Allowed claim:

```text
this candidate stack produces these bounded finite output differences under
these tested orders
```

Still blocked unless separately opened:

```text
flux
Xi/Phi0
Axis0
FEP/Holodeck
physics/gravity
final manifold admission
```

## Enforcement Rule

Any new order/nesting result must include:

```text
parent_completion_receipts
parent_completion_status
why_each_parent_is_complete_for_this_test
finite_map
domain
codomain_or_output
F01 witness
N01 witness
common carrier/projection
controls
ablation_outcome_delta
blocked consumers
claim ceiling
```

If `parent_completion_status` is missing, stale, or only `bounded_scout`, the
order/nesting test is blocked.

