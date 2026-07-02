# Formal Sim Actual Layer Factory Standard - 2026-05-28

Status: active standard for the formal manifold layer-lego factory. This is a
process/control document, not a sim result, not Axis0 closure, not flux closure,
not FEP/Holodeck admission, not gravity proof, and not final manifold
completion.

## Short Version

Wolfram itself does not matter here.

The useful borrowed idea is a process shape:

```text
generate multiple possible branches
keep branch provenance
test rewrite/order sensitivity
use negative controls to prevent one familiar proxy from taking over
```

That process shape can help one layer packet, but it is not the system, not a
tool requirement, and not a proof surface.

The actual work is:

```text
build every manifold layer as a finite source-native lego
stress each layer across variants/depth/scale
record pass/fail/kill/block/resource-block truth
only then test stacking/order/composition
```

## What We Are Actually Building

The active object is the layer-lego factory:

```text
ManifoldLayerLegoFactoryCampaign
```

It builds independent bounded layer sims before compound claims.

The active layer set is:

```text
L0 response/effect/path quotient PEPS3D entropy layer
L1 PEPS3D closure/environment/boundary-MPS layer
L2 spinor/chirality/Weyl cover layer
L3 Clifford/quaternion invariant layer
L4 terrain/channel/generator layer
L5 operator-substage PEPS3D cell layer
L6 entropy/cut/communication layer
L7 Hopf/fibration/shell projection layer
L8 gluing/groupoid/equivariant/dynamic candidate layer
```

Each layer is not "done" because one compact scout passed. A layer needs depth,
variant, tool-ablation, scale, and control coverage, or a precise blocker.

The immediate next artifact is a repaired layer matrix:

```text
system_v5/ops/formal_scouts/layer_lego_factory_repair_matrix_20260528.json
system_v5/ops/formal_scouts/layer_lego_factory_continuation_20260528.json
```

That matrix must reconcile the old compact L0-L8 receipts, the L4/L5/L7 depth
packet, later M_RPF/post-stack/bond/Wolfram receipts, and the shell-gradient
alignment patch. After that, it must name the next independent per-layer row.

## What Counts As A Layer Lego

A layer lego is a bounded finite sim with an exact map:

```text
finite_map:
  domain -> codomain_or_output
```

It must include:

```text
layer_id
variant_id
finite_map
domain
codomain_or_output
root_constraints_in_force
F01 finite carrier/probe/operator/path witness
N01 noncommuting/order-sensitive witness
PEPS3D K=(V,E,F,C) anchor
torch-native spinor or spinor-derived density where applicable
quaternionic map/invariant where quaternion language appears
source-native spinor/PEPS3D checks
shell-gradient fields where shell/Axis0/FEP/gravity/flux language appears
tool manifest and integration depth
non-vacuous ablation_outcome_delta
8/16/32/64 qubit/site stress or resource_blocker
negative controls
blocked consumers
result path
next action
```

If a sim cannot state the finite map, it is not a layer lego. If it only names a
layer, it is label-only.

## Source-Native Carrier Requirements

For nonclassical manifold work, the carrier is not an ordinary dense state with
a fancy label.

A good carrier has:

```text
finite PEPS3D K=(V,E,F,C) from the start
torch complex spinor payloads or spinor-derived densities
local PEPS3D site/bond/face/cell anchoring
noncommuting or order-sensitive operator/path family
QIT density/cut/channel/path readouts only where provenance is present
explicit dense-state, NumPy, Cartesian, and scalar-label controls
```

PEPS3D is not a late display layer. It is the finite locality/cell carrier for
the source-native spinor network used by the layer map.

## What PEPS3D Means Here

PEPS3D is not a magic word and not currently a standalone repo package called
`peps3d`.

The claim-bearing object is a spinor network, not a generic tensor network.
PEPS3D supplies the finite three-dimensional locality/cell structure that lets
the spinor network run without collapsing into dense-state closure or labels.
Tensors are implementation coordinates for spinors, channels, and local maps;
they are not the primitive object being claimed.

The math meaning is a three-dimensional projected-entangled-pair-state style
locality carrier for spinor data:

```text
K = (V, E, F, C)

V = finite site anchors
E = finite virtual bonds / adjacency links
F = finite faces / boundary patches
C = finite 3D cells / local carrier volumes
psi_v = local spinor at site v
rho_v = spinor-derived local density where a density readout is needed
A_v / K_v = local operator, channel, or terrain action at site/cell v
chi_e = virtual bond dimension on edge e
d_v = physical/spinor dimension at site v
```

In this project PEPS3D is stricter than PEPS-as-generic-tensor-network. A
PEPS3D claim must carry source-native spinor structure:

```text
site/bond/face/cell provenance
complex spinor phase as first-class state
spinor-derived density only as readout or local carrier projection
Hopf fiber/base metadata where used
left/right Weyl or chirality sheet metadata where used
shell radius/orientation metadata where shell language appears
local channel/operator/terrain actions when those layers are being tested
boundary/cut readouts tied to the carrier, not scalar summaries
```

The runtime meaning is concrete:

```text
PyTorch tensors
  represent spinors, spinor-derived densities, local channels, gradients, and
  QIT readouts; tensor storage is the implementation, not the claimed object

quimb.tensor / quimb.tensor.PEPS3D
  may construct an explicit PEPS3D locality/network object when the packet needs
  a PEPS3D carrier rather than only a site/bond table; it does not by itself
  prove a source-native spinor network

cotengra or opt_einsum
  may carry local contraction-tree or contraction/readout evidence; full-network
  contraction must be stated separately and is not implied by local contraction
  witnesses; contraction evidence is subordinate to spinor provenance

rustworkx / PyG / XGI
  may carry graph, message-passing, or hypergraph locality over the same finite
  carrier

TopoNetX / GUDHI
  may carry cell-complex and topology/persistence evidence over the same carrier
```

So the actual tool that "runs PEPS3D" depends on the claim:

```text
spinor payload / spinor-derived density / autograd / QIT readout -> PyTorch
explicit PEPS3D locality object -> quimb.tensor.PEPS3D when used
contraction witness -> cotengra or opt_einsum
graph-local dynamics -> PyG or rustworkx
cell/face/topology validity -> TopoNetX / GUDHI / XGI where relevant
finite proof gate -> z3 / cvc5 / SymPy
```

If a packet says PEPS3D but has no finite site/bond/face/cell carrier, no
torch-native spinor payload or spinor-derived density, no spinor phase/chirality
provenance where relevant, no locality/topology/contraction evidence, and no
controls that erase or scramble those structures, then it is not PEPS3D evidence.
It is a label. If it has tensors but no spinor provenance, it is also not
source-native manifold evidence.

Minimum PEPS3D evidence for a formal sim:

```text
shape: e.g. 2x2x2, 4x4x4, or named finite shell/cell complex
site_count: 8/16/32/64 where the packet's scale target requires it
bond_dim: explicit virtual bond dimension
physical_dim: explicit spinor/density/channel dimension
spinor_payloads: per-site psi_v or spinor-derived rho_v with phase/provenance
implementation_shapes: tensor/storage shapes for the spinor payloads and maps
finite map: domain -> codomain/output
carrier action: local spinor/channel/operator/terrain update or contraction/readout
readouts: QIT entropy/cut/order/local-environment values tied to the carrier
controls: spinor phase erased, PEPS label erased, topology shuffled,
          shell orientation erased, bond/site collapse, scalar-summary-only,
          dense-state closure rejected
tool ablation: removing the load-bearing tensor/topology/proof tool fails,
               weakens, or makes the claim unprovable
claim ceiling: explicit statement of what PEPS3D claim is not proven
```

The existing 64-site scout is a useful example of a bounded PEPS3D carrier
receipt: `system_v5/ops/formal_scouts/sim_peps3d_64_site_no_dense_environment_topology_flux_probe.py`
builds a `4x4x4` carrier with 64 local tensor-storage payloads, `bond_dim=2`, a
`quimb.tensor.PEPS3D` object, local environment readouts, topology controls, and
an explicit block on dense full-state closure and final PEPS3D contraction. That
is bounded PEPS3D locality evidence. It is not enough by itself to prove a
source-native spinor-network manifold layer unless the packet also preserves the
spinor payload, phase/chirality provenance, and relevant local spinor actions.

## Shell-Gradient Requirements

If a layer uses shell, future possibility, Axis0, FEP, gravity, or flux
language, it must preserve the literal shell possibility-gradient object:

```text
Sigma_r(x) shell stack
i/r shell order
Omega_r(x) future possibility set
j/k future-fuzz indices
future-inward orientation
past-outward record orientation
rho_Br boundary density
rho_IrBr compatible interior-boundary density
compatibility weights
compression into rho_present
outward record
readout provenance
```

Axis0 is downstream and vector-first:

```text
A0_raw = (
  Delta H_Omega,
  Delta S_B,
  Delta K,
  order_gap,
  chirality_sheet
)

Phi0 = discovered projection(A0_raw)
```

So scalar entropy, coherent information, logZ, FEP, PEPS3D, or Wolfram-style
branching can be readouts/adapters only. They cannot replace the object.

## Actual Tool Stack

Use tools because they can change, constrain, certify, or falsify a layer claim.
Imports do not count.

### Numeric And Differentiable Carrier

```text
PyTorch
  primary tensor substrate
  complex spinors
  density matrices
  channels/operators
  autograd gradients
  QIT readouts

quimb.tensor
  explicit PEPS/MPS/PEPS3D network construction where a tensor-network object
  is itself part of the claim

cotengra
  contraction-tree search and local contraction-width/cost witnesses

opt_einsum
  explicit tensor contraction recipes, partial traces, and cut readouts

PyG
  graph/message-passing computation on finite carrier graphs
  useful when the layer has graph-local dynamics, not just a graph label
```

### Proof And Constraint

```text
z3
  finite constraint checks
  SAT/UNSAT structure gates
  noncommutation/order-collapse claims
  downstream-lock impossibility checks

cvc5
  independent SMT cross-check
  finite operator/search/synthesis checks where relevant
  second proof surface when z3 alone is too easy to overtrust
```

### Symbolic Math

```text
SymPy
  symbolic identities
  closed-form sanity checks
  formula derivations
  exact small-case algebra
```

### Geometric Algebra And Spinor Structure

```text
Clifford
  Cl(3)/Cl(6)
  geometric product
  rotors/spinors
  chirality and orientation checks
  quaternion/Clifford bridge controls where relevant
```

### Graph And Hypergraph Structure

```text
rustworkx
  fast graph/DAG/order/provenance checks
  dependency and carrier routing
  order-sensitivity witnesses

XGI
  hypergraph and multiway interactions
  shell/face/operator constraints involving more than pairwise edges
```

### Topology

```text
TopoNetX
  cell-complex topology
  PEPS3D V/E/F/C and higher-order cell structure

GUDHI
  filtrations
  persistent homology
  topology across scale/depth variants
```

### Metric And Symmetry When Actually Relevant

```text
geomstats
  Riemannian metrics
  geodesics
  curvature or shell metric checks
  only when a layer makes metric/geodesic/curvature claims

e3nn
  E(3)/O(3)/SU(2)-style equivariant computation
  only when symmetry-native computation is load-bearing
```

### Planned Or Not Currently Claim-Bearing

```text
Lean 4
  planned higher proof layer; not current receipt evidence

TLAPS/TLA+
  planned temporal/liveness proof layer; not current receipt evidence

Wolfram
  not an active proof/tool dependency here
  only process inspiration or an adapter idea if explicitly translated into
  finite branch generation with provenance and controls
```

## What Makes A Tool Load-Bearing

A tool is load-bearing only if removing it causes one of:

```text
claim_fails
claim_weakens_below_threshold
map_unprovable
control_no_longer_collapses
downstream lock cannot be certified
```

Not load-bearing:

```text
imported but unused
used only for formatting
used only to produce a label
duplicates PyTorch without changing the claim
computes a scalar that still passes after object-erasure controls
```

Each result should include:

```text
TOOL_MANIFEST
TOOL_INTEGRATION_DEPTH
tool_ablations
ablation_outcome_delta
```

## What Makes A Sim Good

A good actual sim:

```text
1. declares the finite map
2. declares domain and codomain/output
3. uses F01 and N01 as active constraints
4. uses a finite PEPS3D/spinor carrier from the start
5. has torch-native computation, not NumPy as hidden substrate
6. includes the right tool stack for the layer claim
7. makes at least one non-PyTorch tool load-bearing where relevant
8. runs 8/16/32/64 qubit/site stress or writes a resource blocker
9. computes QIT entropy only where density/cut/channel/path provenance exists
10. includes controls that should kill or weaken the claim
11. records blocked downstream consumers
12. writes source and result artifacts
13. passes contract lint and fresh-rerun validation
14. updates the matrix and continuation
```

## What Makes A Sim Bad

A bad sim:

```text
uses layer names as proof
uses PEPS3D as a label but not a carrier
uses scalar entropy as the object
uses FEP as imported metaphor
uses Axis0 as one scalar
uses Wolfram/ruliad language as authority
uses dense full-state closure for a nonclassical manifold claim
uses NumPy or .numpy() as hidden claim-bearing substrate
imports tools without ablation
passes one scout and marks the campaign complete
runs post-stack before the layer matrix is exhausted
does not write the next exact continuation
```

## Required Controls

Every relevant layer packet should run controls such as:

```text
order-erased control
label-erased control
commuting-path control
dense-closure control
NumPy/classical adapter block
PEPS3D label-only control
spinor phase erased
Hopf fiber/base erased
left/right Weyl sheet erased
shell radius/order erased
future-inward/past-outward orientation erased
Omega_r scrambled with counts preserved
scalar entropy primary
FEP decorative label
Axis0 scalar proxy
Wolfram/ruliad primary-object substitution
```

A claim survives only if the real structure matters and the proxy versions fail
or weaken.

## Scale Standard

Minimum stress ladder:

```text
8 sites/qubits
16 sites/qubits
32 sites/qubits
64 sites/qubits
```

If a layer cannot reach a rung, the result must say:

```text
resource_blocked
blocked rung
exact reason
smallest next admissible test
```

No toy-only layer is allowed to become complete.

## Output Artifacts

Each bounded layer packet should produce:

```text
system_v5/ops/formal_scouts/sim_<layer>_<variant>_probe.py
system_v5/ops/formal_scouts/results/<layer>_<variant>_probe_results.json
matrix update in layer_lego_factory_repair_matrix_20260528.json
continuation update in layer_lego_factory_continuation_20260528.json
```

The result JSON must carry enough fields that another agent can audit it
without believing the prose summary.

## Validation Commands

Use the repo interpreter from the Makefile when running sims. At closeout,
minimum validation is:

```text
python3 scripts/wizard_v4_3_object_preservation.py validate --input system_v5/ops/formal_scouts/layer_lego_factory_v43_object_packet_20260528.json
python3 scripts/lint_sim_contract.py <touched scout files>
python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py --fresh-rerun <touched result files>
python3 -m json.tool <touched json files>
git diff --check
```

If a sim invokes shell-field claims, also validate against the RPF object packet:

```text
python3 scripts/wizard_v4_3_object_preservation.py validate --input system_v5/ops/formal_scouts/retrocausal_shell_field_v43_object_packet_20260527.json
```

## Status Labels

Use status labels narrowly:

```text
exists
runs
passes local rerun
canonical by process
blocked_with_receipt
resource_blocked
killed
queued_with_continuation
```

Do not say:

```text
verified
proved
complete
canonical
final manifold
Axis0 admitted
physics aligned
```

unless the exact gate and receipt support that stronger claim.

## Enforcement Rule

The enforcement rule is:

```text
If the next step is post-stack, bond, Wolfram, Axis0, FEP, flux, physics,
or final manifold before the repaired layer matrix proves all layer-depth and
variant rows are accounted for, the step is invalid and must be demoted.
```

The next valid formal work is therefore:

```text
build/update the layer-factory repair matrix
pick the next independent per-layer depth/variant row
run or block exactly one bounded layer packet
validate
update matrix and continuation
continue
```
