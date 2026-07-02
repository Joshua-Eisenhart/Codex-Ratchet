# Formal Sim Layer Variant Constraint Alignment Spec - 2026-05-26

Purpose: make the formal lane build every candidate manifold layer as a lego, with variants, before proving stacking order.

This is not a phase-closeout artifact and not an admission receipt. It is a controller spec for the next formal sim goal. The compact launch prompt may reference this file when it cannot fit the whole layer x variant x constraint matrix.

## Substrate Precondition

Do not adopt this whole matrix as the controlling launch surface until the
substrate legos can populate its required rows honestly.

Current launch order:

1. Reconcile/admit or block the existing `system_v5/legos/` torch lego receipts
   against `system_v5/docs/MIGRATION_REGISTRY.md` and
   `system_v5/docs/TOOL_LEGO_INTEGRATION_MATRIX.md`.
2. Build missing substrate legos first, especially density matrix, CNOT or an
   equivalent two-qubit entangling gate, depolarizing/CPTP channel, and
   spinor-to-density or chiral-overlap bridge.
3. Only then use this matrix as a tracker for variants of earned legos.

If the substrate registry still says a prerequisite is `NOT_STARTED`, a matrix
row depending on that prerequisite is `blocked_on_substrate`, not `passed`.

## Core Correction

The active unit is not "one layer row". The active unit is:

```text
layer_id x variant_id x scale_rung x tool_receipt
```

Each layer must run multiple variants. A single representative probe cannot pass the layer. Stacking/order is later work. The formal lane should first make the lego inventory.

The inventory is not only the seven current rows. It includes possible geometries and possible G-structures that may later be killed, blocked, or excluded. A killed geometry is useful evidence. A geometry that never ran is not evidence.

1. PEPS3D closure lego variants.
2. Hopf/Weyl spinor shell lego variants.
3. Quaternion invariant lego variants.
4. Terrain placement lego variants.
5. Operator substage cell lego variants.
6. Entropy geometry lego variants.
7. Tensor communication lego variants.
8. Candidate geometry and G-structure legos, including rejected candidates.

Every variant must either pass the universal gates below or write a blocker with exact failed gate, failed scale, failed tool, and next admissible repair.

## Universal Variant Schema

Every matrix row and result receipt must expose these fields:

```json
{
  "schema_version": "layer_lego_v1",
  "field_alias_policy": "forbidden",
  "sim_id": "",
  "tier": "",
  "sim_execution_kind": "nonclassical",
  "layer_id": "",
  "variant_id": "",
  "variant_axis": "",
  "geometry_family": "",
  "g_structure_family": "",
  "possible_geometry_status": "candidate|passed|killed|blocked|excluded",
  "tranche_id": "T1|T2|T3|T4",
  "finite_map": "",
  "domain": "",
  "codomain_or_output": "",
  "F01_alignment": "",
  "N01_alignment": "",
  "extended_constraint_alignment": {},
  "peps3d_embedding": "",
  "spinor_state": "",
  "quaternion_action": "",
  "required_entropy_families": [],
  "entropy_matrix": [],
  "cut_registry": [],
  "communication_registry": [],
  "basis_probe_registry": [],
  "entropy_control_matrix": [],
  "entropy_scale_status": {},
  "required_tools": [],
  "actual_tools_used": [],
  "tool_manifest": {},
  "tool_integration_depth": {},
  "load_bearing_tools": [],
  "tool_ablations": [],
  "tool_relevance_matrix": {},
  "scale_rungs": [],
  "toy_allowed": false,
  "controls": [],
  "required_negatives": [],
  "negatives_run": [],
  "negative_conditions": [],
  "kill_conditions": [],
  "required_artifacts": [],
  "artifacts_emitted": [],
  "witness_trace_id": "",
  "result_summary": {},
  "promotion_status": "admitted|keep_but_open|audit_further|diagnostic_only|broken",
  "public_status_label": "exists|runs|passes local rerun|canonical by process",
  "runner_state": "not_started|queued|running|passed|killed|blocked|resource_blocked",
  "blocker_reason": "",
  "receipt_path": "",
  "missing_probes_count": 0,
  "admissibility_criteria": [],
  "classification": "",
  "eligible_consumers": [],
  "blocked_consumers": []
}
```

No aliasing is allowed. For example, do not mix `codomain`, `codomain_or_output`, `F01_set`, `F01_alignment`, `pass_fail`, and `status` as interchangeable fields. If a worker uses aliases, the row is schema-failed until repaired.

## Candidate Geometry And G-Structure Inventory

The matrix must contain rows for possible geometries, not only rows for the currently favored story. Each entry is a lego candidate, not canon.

Minimum geometry families to enumerate:

- finite_probe_response_quotient_geometry;
- complex_hilbert_density_carrier;
- peps3d_tensor_network_geometry;
- mps_mera_boundary_mps_geometry;
- unit_spinor_sphere;
- projective_base_sphere;
- hopf_fiber_bundle;
- hopf_torus_leaf_family;
- connection_holonomy_geometry;
- weyl_chirality_orientation_cover;
- clifford_module_geometry;
- quaternionic_action_geometry;
- frame_bundle_g_structure_reduction;
- symplectic_contact_poisson_dirac_family;
- berry_phase_connection_geometry;
- finite_spectral_triple_nc_geometry;
- equivariant_representation_geometry;
- sheaf_gerbe_groupoid_gluing_geometry;
- terrain_metric_placement_geometry;
- operator_substage_cell_geometry;
- entropy_cut_geometry;
- tensor_communication_geometry;
- dynamic_transition_ratchet_geometry.

Minimum G-structure families to enumerate where finite-mapable:

- O(n), SO(n), SO(p,q);
- U(n), SU(n);
- Sp(n), Sp(n).Sp(1);
- Spin(n), Spin(p,q), Spin^c, Pin+, Pin-;
- orientation, time-orientation, chirality/CPT-sector discrete structures;
- G2 and Spin(7) as exploratory exceptional candidates only when a finite map and controls exist;
- Cartan/Klein/parabolic reductions where a finite model pair and reduction map are explicit.

For each candidate, record:

- `candidate_reason`: why this candidate might matter;
- `finite_mapable`: true/false;
- `first_probe`: smallest admissible probe;
- `kill_condition`: what would exclude it;
- `entropy_network_required`: true/false with reason;
- `stacking_input_allowed`: always false until later stacking prompt.

Do not add exceptional or abstract structures as decoration. If a finite carrier, map, controls, and tool path cannot be named, mark the candidate blocked or excluded.

## Root Constraint Gates

F01 finite gate:

- finite carrier set;
- finite probe/effect set;
- finite operator/path set;
- explicit domain and codomain;
- finite PEPS3D carrier anchor K=(V,E,F,C);
- finite scale ladder with 8 as floor and 16/32/64 as stress rungs where possible;
- no dense-state or infinite continuum closure as claim-bearing evidence;
- if a scale rung fails for resource reasons, write a resource blocker, not a pass.

N01 noncommutation/order gate:

- at least one nonzero order gap, commutator gap, channel-order gap, path-order gap, or history-effect gap;
- order-erased and commuting controls collapse;
- label-only, scalar-only, Bloch-only, and non-informational controls fail or stay blocked;
- if a row has no possible N01 witness, it is a classical/control row and cannot carry nonclassical manifold evidence.

## Extended Constraint Gates

Each variant must check all applicable extended gates. Non-applicable gates must be marked `not_applicable` with a reason.

| Gate | Required check |
| --- | --- |
| EC_density | Density is Hermitian, positive semidefinite, trace-one; spinor-derived density is distinguished from arbitrary standalone density. |
| EC_CPTP | Channels have Kraus/Choi/CPTP checks or are explicitly blocked as non-CPTP controls. |
| EC_PEPS3D | K=(V,E,F,C) anchors are explicit; site/edge/face/cell supports are nonempty where claimed; no scalar PEPS3D labels. |
| EC_chirality | L/R or Weyl chirality data is explicit; chirality-swapped and no-chirality controls are present. |
| EC_quaternion | Quaternion/Clifford action or invariant is explicit; label-only quaternion words fail. |
| EC_entropy | Entropy readouts are QIT aligned: von Neumann spectrum, MI, conditional, relative, coherent info, negativity where applicable; diagonal Shannon is adapter/control only. |
| EC_tool | Full PyTorch tensors for claim-bearing numerics plus at least one non-PyTorch load-bearing tool with ablation. |
| EC_scale | Less than 8 qubits/sites is debug only; 8 is floor; 16/32/64 stress ladder is run or resource-blocked. |
| EC_controls | Product, maximally mixed, order-erased, boundary-shuffled, scalar-label, dense-closure, and Bloch-only controls are present where meaningful. |
| EC_boundary | Blocked consumers are explicit: no Axis0, flux, Xi/Phi0, Holodeck/FEP, physics, final manifold, or stacking claims without later receipts. |

Additional machine gates:

- `EC_geometry_inventory`: every geometry/G-structure candidate row is passed, killed, blocked, excluded, queued, or running. Unlisted candidates are missing work, not absent evidence.
- `EC_entropy_coverage`: every meaningful `layer_id x variant_id x scale_rung` has an entropy matrix entry for required QIT observables or an explicit not-applicable reason.
- `EC_entropy_basis_probe`: diagonal Shannon or basis-dependent entropy is control-only unless basis/probe and matched comparator are explicit.
- `EC_entropy_chirality`: chirality-bearing rows run L, R, L/R, chirality-swapped, and no-chirality entropy partitions.
- `EC_entropy_communication`: communication-bearing rows run entropy/MI/coherent-info over forward, reverse, shuffled, and order-erased directions.
- `EC_tool_relevance`: every relevant tool is `required`, `supportive`, or `not_applicable_with_reason`; load-bearing tools require ablation outcome `claim_fails`, `claim_weakens_below_threshold`, or `map_unprovable`.
- `EC_multitool_consistency`: major geometry claims require at least two load-bearing tools from different mathematical categories or an explicit blocker.
- `EC_scale_asymptotic_stability`: scale rungs report stability, convergence, or instability; lower-rung success is not inherited upward.
- `EC_dual_status`: internal promotion status and public repo truth label stay separate.
- `EC_global_boundary_lock`: `stacking_unlocked=false`, `axis_flux_unlocked=false`, and `physics_unlocked=false` until later receipts explicitly unlock them.

## Entropy Spinor Network Harness

Entropy is not one later layer. It is a readout harness run across every meaningful layer and possible geometry.

For every candidate row, build or block:

```json
{
  "required_entropy_families": [
    "von_neumann",
    "renyi2",
    "mutual_information",
    "conditional_entropy",
    "relative_entropy",
    "coherent_information",
    "negativity",
    "log_negativity",
    "path_entropy"
  ],
  "entropy_matrix": [
    {
      "observable": "",
      "status": "required|passed|killed|blocked|not_applicable|control_only",
      "support_kind": "site|edge|face|cell|sheet|boundary|path|history",
      "support_id": "",
      "subsystem_partition": "",
      "geometry_cut_id": "",
      "channel_context": "pre_channel|post_channel|order_swap|boundary_restricted|forward|reverse|shuffled|order_erased",
      "chirality_partition": "none|L|R|LR|swapped|no_chirality_control",
      "basis_or_probe": "",
      "artifact_paths": [],
      "blocked_reason": ""
    }
  ]
}
```

Required controls per observable where meaningful:

- product state;
- maximally mixed state;
- matched-marginal product;
- order-erased path;
- boundary-shuffled cut;
- chirality-swapped or no-chirality carrier;
- Bloch-only adapter;
- scalar PEPS label;
- dense-state/dense-environment closure.

If entropy appears to be geometric, the receipt must say which support made it geometric: site, edge, face, cell, sheet, boundary, path, or history. A scalar entropy number without support/cut/probe is not geometry.

## Terrain Variant Harness

Each terrain is its own simmable placement law, not just a label attached to an engine.

Terrain rows must include variants across:

- terrain family: Se, Ne, Ni, Si, plus label-erased and randomized controls;
- law form: unitary, CPTP/Kraus, Lindblad-small-step, projector/invariant-subspace, metric-distortion, curvature-induction;
- support: site, edge, face, cell, local patch, boundary;
- order: terrain then operator, operator then terrain, terrain-pair order, order-erased;
- basis: aligned, perturbed, swapped, random;
- entropy: bulk cut, boundary cut, L/R sheet cut, path-history cut;
- scale: 8/16/32/64 sites or qubits, with resource blockers for failed rungs.

Terrain pass requires a finite map from terrain law to carrier readout, at least one nonzero terrain/order witness, entropy or boundary effect where meaningful, and collapse under terrain-erased/label-only controls.

## Tranche Execution Rule

The matrix can be large. Avoid metadata churn by terminalizing tranches:

- T1: one bootstrap probe per geometry family or variant axis at scale 8 with root controls.
- T2: one stress rung at >=16 or a resource blocker.
- T3: one non-PyTorch load-bearing tool ablation receipt.
- T4: entropy spinor network coverage on required cuts/partitions.

Do not add a new variant axis to a geometry family until the prior tranche has terminal states: `passed`, `killed`, `blocked`, or `resource_blocked`.

Bootstrap exception: if the current matrix version has zero runner receipts, allow one bounded scale-8 bootstrap probe per geometry family even if the old reset lock would otherwise create a no-run loop. After bootstrap receipts exist, strict gates resume. This is not downstream permission.

## Layer Variant Matrix

### L0 finite_probe_response_quotient_geometry

Goal: keep the root geometry visible before richer carriers are tested.

Required variants:

- finite probe/effect quotient family;
- finite history/process POVM family;
- projective/incidence geometry family;
- Weyl-Heisenberg or Pauli path family;
- noncommuting and order-erased controls;
- response-equivalence quotient controls: empty probe, single non-informational probe, non-IC subset.

Load-bearing tools: PyTorch for carrier/readout, z3/cvc5 for finite response distinctions, SymPy for exact tiny checks, graph tools for incidence/path supports.

Pass requires: finite response quotient geometry with F01/N01, not physical manifold closure.

### L0b complex_hilbert_density_carrier

Goal: test complex Hilbert space and density matrices as early working carriers without claiming they are root-forced.

Required variants:

- pure spinor, mixed spinor-derived density, arbitrary density control;
- Hermitian/PSD/trace-one checks;
- CPTP evolution and non-CPTP blocker;
- product and entangled controls;
- entropy matrix on spinor-derived cuts.

Pass requires: density is valid carrier data and distinguished from arbitrary standalone density.

### L1 peps3d_closure

Goal: prove finite PEPS3D carrier closure as a lego, not just anchor labels.

Required variants:

- shape variants: 2x2x2, 2x2x4, 2x4x4, 4x4x4 or equivalent 8/16/32/64 site rungs;
- bond variants: chi=2, chi=4, chi=8 where resources allow;
- support variants: site, edge, face, cell, local star, local patch;
- boundary variants: open boundary, periodic-control boundary, boundary-erased control, boundary-shuffled control;
- contraction variants: finite local contraction, finite boundary-MPS/SVD truncation, dense-closure control.

Load-bearing tools: PyTorch/autograd, PyG, rustworkx, XGI, TopoNetX, GUDHI, z3/cvc5 for finite anchor constraints.

Pass requires: finite K anchors, finite-chi readouts, N01 order witness on anchored paths, and collapse under anchor/order erasure.

### L2a unit_spinor_sphere

Goal: build unit spinor geometry as finite carrier/readout, not Bloch-sphere leakage.

Required variants:

- spinor norm and phase/gauge variants;
- spinor -> density variants;
- gauge variants: phase/gauge-invariant observable, gauge-scrambled control;
- Bloch adapter control: Bloch-only readout must not carry the claim.

Load-bearing tools: PyTorch complex tensors, Clifford/Geometric algebra if available, SymPy for symbolic spinor checks, z3/cvc5 for finite sheet constraints.

Pass requires: finite spinor readout with gauge controls and Bloch-only collapse.

### L2b hopf_fiber_bundle_and_tori

Goal: test Hopf projection, fiber, and torus leaf families as finite shell geometry.

Required variants:

- projective base sphere readout;
- fiber phase readout;
- nested shell index n=0/1/2 or bounded finite shell set;
- hopf torus leaf family;
- connection/holonomy path family;
- fiber-erased and base-erased controls.

Pass requires: finite Hopf/fiber readout that changes under noncommuting path/connection choices and collapses under erased controls.

### L2c weyl_chirality_orientation_cover

Goal: test L/R Weyl sheets and orientation cover separately from generic spinor data.

Required variants:

- L sheet, R sheet, L/R paired carrier;
- chirality-swapped control;
- no-chirality control;
- orientation/time-orientation candidate controls;
- entropy over L, R, and L/R partitions.

Pass requires: chirality-sensitive finite readout with controls; no label-only chirality.

### L3 quaternion_invariant

Goal: build quaternionic action/invariant as a finite map.

Required variants:

- input variants: spinor input, spinor-derived density input, PEPS3D local tensor input;
- action variants: left quaternion action, right quaternion action, conjugation/rotor action;
- invariant variants: norm, phase/gauge class, commutator, sheet-sensitive invariant;
- control variants: identity quaternion, commuting quaternion, label-only quaternion, random scalar label.

Load-bearing tools: Clifford or geometric algebra, PyTorch, SymPy, z3/cvc5 for finite algebra constraints.

Pass requires: quaternion action changes an admitted finite readout in a controlled way and controls collapse.

### L3b clifford_module_and_g_structure

Goal: test Clifford modules and G-structure reductions as candidate geometries.

Required variants:

- Cl(3), Cl(6), Spin, Spin^c, Pin candidates where finite-mapable;
- O/SO/U/SU/Sp reduction candidates;
- torsion/obstruction readouts where finite-mapable;
- G2/Spin(7) exploratory rows only with finite controls;
- label-only group controls.

Pass requires: finite group/action/reduction map, invariant or obstruction readout, and tool-backed controls.

### L3c symplectic_contact_poisson_dirac

Goal: test symplectic/contact/Poisson/Dirac/Berry-form candidates without promoting flux.

Required variants:

- symplectic form or Berry form on finite carrier;
- contact/Sasakian/CR branch only when finite-mapable;
- Poisson bracket or Dirac structure readout;
- closed-form/exact-form controls;
- order/path entropy witness where meaningful.

Pass requires: finite form/bracket map and collapse under degenerate/erased controls. Flux remains blocked.

### L3d finite_spectral_triple_nc_geometry

Goal: test finite noncommutative geometry as algebra/module/Dirac lego.

Required variants:

- finite algebra A;
- finite Hilbert/module carrier H;
- finite Dirac operator D;
- bounded commutator readout;
- zero-Dirac, commutative, and negative-effect controls.

Pass requires: bounded finite commutator geometry and controls.

### L4 terrain_placement

Goal: terrain is placement law on carriers, not an engine/operator label.

Required variants:

- terrain variants: Se, Ne, Ni, Si as separate finite placement/channel laws;
- channel variants: unitary, CPTP/Kraus, Lindblad-small-step, projector/invariant-subspace;
- order variants: terrain then operator, operator then terrain, terrain-erased control;
- chart variants: inner/outer placement where documented, axis-3 placement where applicable;
- basis variants: aligned basis, perturbed basis, swapped-basis control.

Load-bearing tools: PyTorch, SymPy, z3/cvc5, Clifford, graph/topology tools for placement constraints.

Pass requires: placement changes admissible carrier readouts, N01 terrain/operator order witness exists, label-erased terrain fails.

### L5 operator_substage_cell

Goal: embed substages as local PEPS3D-carried cells, tensors, or channel actions.

Required variants:

- coverage variants: all 64 operator rows or explicit blocked subset map;
- embedding variants: local cell tensor, local channel action, projection from richer PEPS3D carrier;
- order variants: substage order, reversed order, commuting-only control;
- coupling variants: within-engine, between-neighboring-cells, boundary-cell;
- erasure variants: operator-erased, cell-erased, stage-label-only.

Load-bearing tools: PyTorch, PyG, rustworkx/XGI, z3/cvc5, SymPy.

Pass requires: each claimed substage has finite map, local support, N01 witness or control classification, and no stage-label-only pass.

### L6 entropy_geometry

Goal: test whether entropy is geometric on each layer as QIT information flow, not diagonal Shannon bookkeeping.

Required variants:

- cut variants: site-site, sheet-sheet, edge cut, face cut, cell patch, path/history cut;
- entropy variants: von Neumann, Renyi-2 where applicable, mutual information, conditional entropy, relative entropy, coherent information, negativity/log-negativity where applicable;
- flow variants: before/after local channel, before/after order swap, before/after boundary restriction;
- controls: product state, maximally mixed state, diagonal-only Shannon adapter, Bloch-only adapter, matched-marginal product control.

Load-bearing tools: PyTorch eigensolvers/autograd, SymPy for analytic small cases, z3/cvc5 for finite cut constraints, PyG/graph tools for cut definitions.

Pass requires: entropy readout is tied to PEPS3D/spinor/chirality supports and changes under noncommuting/order paths while controls collapse.

### L7 tensor_communication

Goal: test communication across the tensor network as finite information transfer.

Required variants:

- communication variants: bond message, face message, cell message, sheet-to-sheet message, path-history message;
- direction variants: forward, reverse, shuffled, order-erased;
- network variants: line, grid, cube, hyperedge overlay;
- scale variants: 8/16/32/64 sites with finite chi sweep;
- controls: disconnected graph, shuffled boundary, product carrier, scalar-label channel.

Load-bearing tools: PyTorch, PyG, rustworkx, XGI, TopoNetX, GUDHI, z3/cvc5.

Pass requires: finite communication readout, entropy/MI or coherent-info witness, N01 order/path sensitivity, graph/topology ablation.

### L8 gluing_equivariant_dynamic_candidates

Goal: keep possible but unearned gluing, equivariance, and dynamic transition geometries in the inventory.

Required variants:

- sheaf restriction maps on finite covers;
- gerbe/cocycle obstruction controls where finite-mapable;
- groupoid/action groupoid readouts;
- equivariant representation rows for SU(2), SO(3), E(3)/O(3) where finite;
- dynamic transition/hysteresis/ratchet rows kept pre-basin and blocked from Axis0/physics.

Pass requires: finite covers/actions/transitions with controls. If finite maps are missing, mark blocked or excluded rather than deleting.

## Tool Integration Validity

A tool is load-bearing only when removing it changes the conclusion or blocks the claimed finite map.

Minimum per variant:

- PyTorch is load-bearing for the actual tensor/state/channel computation.
- One algebra/solver/topology/graph tool is load-bearing for a distinct claim.
- `tool_ablations` shows what fails without each load-bearing tool.
- `supportive` tools may format, cross-check, or visualize, but cannot be counted as claim-bearing.

Suggested tool roles:

| Tool | Claim-bearing role |
| --- | --- |
| PyTorch | complex tensors, spinors, density matrices, PEPS3D local tensors, channels, entropy spectra, autograd. |
| PyG | graph-carried tensor/message passing, local cell adjacency, schedule graph operations. |
| rustworkx | finite graph paths, cuts, order/path witnesses, graph isomorphism controls. |
| XGI | hyperedge and cell-complex style carrier checks. |
| TopoNetX | simplicial/cell incidence checks for V/E/F/C carrier structure. |
| GUDHI | persistent/topological readouts over finite filtrations. |
| Clifford/geometric algebra | spinor, Weyl, quaternion, rotor, and chirality actions. |
| SymPy | exact small symbolic reductions and sanity identities. |
| z3/cvc5 | finite constraint satisfiability, blockers, and control impossibility checks. |

## Closeout Rule

A formal run is advancing only if it creates or updates the layer-variant matrix, runs or queues concrete variant probes, and records for each variant:

- root alignment;
- extended alignment;
- candidate geometry/G-structure inventory status;
- scale status;
- tool integration status;
- entropy status where meaningful;
- terrain variant status where meaningful;
- runner state and blocker reason;
- pass/fail/blocker;
- next concrete variant or repair.

It is not advancing if it only adds another Phase 2 row on the same carrier map, only repairs metadata, only writes a transition artifact, only enumerates a matrix without runner receipts or queued probes, or stops after one passing probe while unrun variants remain.

Before any stacking prompt exists, all stacking fields stay locked:

```json
{
  "stacking_unlocked": false,
  "axis_flux_unlocked": false,
  "physics_unlocked": false
}
```
