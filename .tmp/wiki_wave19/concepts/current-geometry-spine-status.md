---
title: Current Geometry Spine Status
created: 2026-04-11
updated: 2026-04-16
type: summary
framing: current
tags: [reference, research, geometry, spine, status, planning]
sources:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/16_lego_build_catalog.md
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/17_actual_lego_registry.md
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/07_model_math_geometry_sim_plan.md
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/08_aligned_sim_backlog_and_build_order.md
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/sim_backlog_matrix.md
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/sim_truth_audit.md
---

# Current Geometry Spine Status

## Purpose
This page gives an as-of snapshot of the geometry spine in the order the system currently wants to build it.

It is not an axis page.
It is not a bridge page.
It is not a final doctrine page.
It is a status page for the pre-axis geometry/chirality/operator construction spine.

Snapshot rule:
- treat the rows below as planning-grade, dated status buckets
- rerun notes and local anchors are as-of statements, not evergreen final truth

## Build logic
The spine should be read in this order:
1. admitted carrier and density states
2. `S^3` spinor carrier
3. Hopf projection and fiber structure
4. nested Hopf tori
5. left/right Weyl split on the nested tori
6. Pauli/operator action on the Weyl layer
7. loop / connection / transport grammar
8. chirality-differential layer
9. only later, if earned: flux candidates and more compound cycles

## Status vocabulary
This page uses three practical buckets:
- **strong snapshot anchor** — good dated evidence exists and the row is useful as a real build anchor
- **partial** — real work exists, but the layer is still thinner than it should be
- **not landed** — the object is documented, but not yet normalized or not yet strong enough to treat as a build anchor

These are planning buckets, not the public truth-label contract. The controller docs currently use four public truth labels:
- `exists`
- `runs`
- `passes local rerun`
- `canonical by process` (the strongest controller-admission label, not a blanket whole-wiki canon claim)

So a "strong snapshot anchor" here means "good dated queue/truth support for planning"; it does not by itself mean `canonical by process`.

## Current spine status

### 1. Carrier and density-state admission
- `carrier_admission_density_matrix` — **strong snapshot anchor**
- `density_matrix_representability` — **strong snapshot anchor**
- `density_state_space_dc2` — **partial**

Snapshot anchor:
- `density_hopf_geometry_results.json`

Why it matters:
Without the admitted density-state carrier, higher geometry is not yet the geometry of a lawful state space.

### 2. `S^3` spinor carrier and Hopf geometry
- `hopf_geometry` — **strong snapshot anchor**
- `torus_geometry` — **strong snapshot anchor**
- `clifford_geometry` — **strong snapshot anchor**
- `spinor_geometry` — **strong snapshot anchor**
- `sphere_geometry` — **partial**

Snapshot anchors:
- `hopf_torus_lego_results.json`
- `foundation_hopf_torus_geomstats_clifford_results.json`

Queue parity note:
- the live backlog still treats explicit Hopf-map, fiber-equivalence, connection/holonomy, nested-torus, Weyl/chiral, and Pauli-on-Weyl packets as open follow-on work rather than as closed by this anchor region

### 3. Hopf map, fibers, and connection objects
- `hopf_map_s3_to_s2` — **snapshot-covered** (currently visible anchor in `density_hopf_geometry_results.json`; the visible artifact does not carry its own date field, so treat this as a current cited anchor rather than a self-dated row)
- `hopf_fiber_equivalence` — **partial**
- `hopf_connection_form` — **partial**
- `fiber_loop_law` — **partial**
- `base_loop_law` — **partial**
- `berry_holonomy` — **strong snapshot anchor**
- `holonomy_geometry` — **partial**
- `transport_geometry` — **partial**

This region is still incomplete overall: the explicit Hopf-map packet has a dated covered local anchor, but fiber-equivalence and connection/transport follow-ons remain open.

### 4. Nested Hopf tori
- `nested_torus_geometry` — **partial**

This is important because the current system wants Weyl and later operator placement to run on the nested Hopf torus structure, not on a flattened generic carrier.

### 5. Weyl split and chiral local bookkeeping
- `weyl_chirality_pair` — **partial**
- `chiral_density_bookkeeping` — **partial**

Dated rerun note:
- the latest visible `weyl_spinor_hopf_results.json` artifact (dated 2026-04-16) gives a stronger snapshot local anchor for `weyl_chirality_pair` and `left_right_asymmetry`, but the broader Weyl/chiral packet remains partial rather than closed.

This layer is explicitly needed before later engine promotion, because left/right chirality is not an optional visualization layer. It changes the lawful placement story.

### 6. Pauli/operator layer on the geometry spine
- `pauli_generator_basis` — **partial**
- `left_right_asymmetry` — **partial**
- `local_operator_action` — **partial**
- `clifford_generator_basis` — **partial**
- `channel_cptp_map` — **partial**
- `composition_order_sensitivity` — **partial**

Dated rerun note:
- the cited `lego_pauli_algebra_results.json` artifact gives a stronger snapshot local anchor for `pauli_generator_basis`, but the broader operator packet remains partial rather than closed and the visible artifact does not carry its own date field on this page.
Related late-local note:
- `terrain_family_fourfold` exists in the registry as `not_normalized_yet`, so terrain/placement language should remain downstream of the cleaner operator and loop packets rather than being treated as a settled standalone anchor.

Ratchet note:
- `composition_order_sensitivity` should be read as the non-commutativity discriminator for the geometry stack, not as generic sequencing metadata. Commuting pairs are negative controls; the actual ratchet question is whether swapping shell or operator order changes the admissible witness set.

This is the main region where the operator packet is still thinner than the geometry packet.

### 7. Graph / topology side of the spine
- `graph_geometry` — **partial**
- `hypergraph_geometry` — **strong snapshot anchor**
- `cell_complex_geometry` — **partial**
- `persistence_geometry` — **partial**
- `state_class_binding_geometry` — **strong snapshot anchor**

Snapshot anchors:
- `xgi_family_hypergraph_results.json`
- `toponetx_state_class_binding_results.json`

This is the strongest current graph/topology region, but it is still not broad enough to call the whole graph/cell-complex lane complete.

### 8. PyG / local witness support on the spine
- `werner_local_structure` — **strong snapshot anchor**
- broader PyG graph-native geometry role — **partial**

Snapshot anchor:
- `pyg_dynamic_edge_werner_results.json`

This is useful because PyG now has one strong local anchor, but that does not yet mean PyG is central to the whole geometry spine.

### 9. Flux candidate family
- flux — **not landed as a local lego**

Current placement:
- later than shell-local geometry
- later than local Weyl extraction
- later than local Pauli/operator packet
- likely only honest after multiple manifold layers run on each other

So flux should be read as a later derived manifold/coexistence candidate, not as an early local object.

## Summary judgment
### Strong current anchors
- density-state admission
- Hopf/torus/Clifford/spinor core
- Berry holonomy
- hypergraph shell side
- TopoNetX state-class binding
- PyG Werner local structure

### Partial but important
- nested tori as distinct object
- Hopf map/fiber/connection packet
- Weyl/chiral bookkeeping
- Pauli/operator local packet
- cell-complex/persistence packet
- broader transport/holonomy packet

### Not landed enough yet
- flux as an honest derived family
- several placement/order/operator elaborations that are still only document-level or partial

## Related pages
- [[geometry-manifold-parity-audit]]
- [[sim-build-spine-and-wiki-maintenance]]
- [[aligned-sim-backlog-and-build-order]]
- [[actual-lego-registry]]
- [[lego-build-catalog]]
- [[constraint-on-distinguishability-full-math]]
- [[terrain-laws-and-loop-geometry]]
- [[operator-math-explicit]]
- [[pauli-on-weyl-loop-interaction]]
- [[weyl-flux]]
- [[controller-state-transition-model]]
