# QIT Hopf–Weyl Projection (Bounded Read-Only Sidecar)

- generated_utc: `2026-03-27T00:06:39Z`
- source_content_hash: `7d25ff22e49d8606ddb8e5dd8e3ee4b6b1cce934fe7da51cd1ad36cc75a768ff`
- do_not_promote: `True`
- mode: `bounded_read_only`

## Report Surface
- surface_class: `tracked_current_workspace_report`
- represents: `current workspace Hopf/Weyl sidecar state at generation time; may differ from the last committed snapshot until tracked CURRENT artifacts are committed`
- git_sha: `cea9e14ec6742760fb8f16f7ca53405ca1ee9de7`

## Owner Graph Inputs
- Torus nodes: `3`
- Engine nodes: `2`
- Macro-stage nodes: `16`
- TORUS_NESTING edges: `2`
- STAGE_ON_TORUS edges: `32`
- CHIRALITY_COUPLING edges: `1`

## 1. TopoNetX Candidate Cell-Complex View
- available: `True`
- shape: `[16, 34, 3]`  (0-cells, 1-cells, provisional 2-cells)
- stage 0-cells: `16`
- torus `inner`: 8 stages in provisional sidecar boundary
- torus `clifford`: 16 stages in provisional sidecar boundary
- torus `outer`: 8 stages in provisional sidecar boundary

## 2. Stage–Torus Cycle Groupings
- fiber stages (inner+clifford): `8`
- base stages (outer+clifford): `8`
- all admitted stages attach to Clifford: `True`
- Clifford is universal bridge in current owner scaffold: `True`
- `inner`: 8 stages
- `clifford`: 16 stages
- `outer`: 8 stages

## 3. Chirality Coupling Candidate Mapping (Cl(3,0))
- available: `True`
- pseudoscalar: `e123`
- Type-1 orientation: `+e123`
- Type-2 orientation: `-e123`
- coupling product is scalar: `True`

## 4. Torus Geometry
- `inner`: R_major=0.9239, R_minor=0.3827, area=0.3536, flatness=0.4142, loop=fiber
- `clifford`: R_major=0.7071, R_minor=0.7071, area=0.5000, flatness=1.0000, loop=bridge
- `outer`: R_major=0.3827, R_minor=0.9239, area=0.3536, flatness=0.4142, loop=base
- Clifford equal-radii under imported constants: `True`
- Normalized eta-separation inner→outer: `1.0`

## 5. Relevant Negative Evidence
- Torus witnesses: `2`
- Chirality witnesses: `2`
- `neg_no_torus_transport` (TORUS, suppressed_pending_owner_concept): Removing torus transport kills the engine
- `neg_torus_scrambled` (TORUS, suppressed_pending_owner_concept): Scrambling torus assignment kills coherence
- `neg_no_chirality` (CHIRALITY, specific_targets): Removing engine type distinction kills asymmetry
- `neg_type_flatten` (CHIRALITY, specific_targets): Flattening engine types kills chirality separation

## Boundary Note
- The tracked __CURRENT__ files represent the current workspace after generation, not automatically the last committed snapshot.

