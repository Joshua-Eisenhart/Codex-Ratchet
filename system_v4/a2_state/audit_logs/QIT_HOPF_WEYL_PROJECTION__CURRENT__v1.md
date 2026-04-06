# QIT Hopf–Weyl Projection (Bounded Read-Only Sidecar)

- generated_utc: `2026-04-01T10:59:59Z`
- source_content_hash: `859aa5c7babcc5057780232f5ffffbd463764180ece8f53dee2cad18e4ffaf36`
- do_not_promote: `True`
- mode: `bounded_read_only`

## Report Surface
- surface_class: `tracked_current_workspace_report`
- represents: `current workspace Hopf/Weyl sidecar state at generation time; may differ from the last committed snapshot until tracked CURRENT artifacts are committed`
- git_sha: `092ec33193f1b18fdf4d5b12da35e08b26f9b50e`

## Owner Graph Inputs
- Torus nodes: `3`
- Engine nodes: `2`
- Macro-stage nodes: `16`
- TORUS_NESTING edges: `2`
- STAGE_ON_TORUS edges: `32`
- CHIRALITY_COUPLING edges: `1`

## Owner Carrier Evidence
- carrier_assignment_scope: `owner_scaffold_only`
- TORUS_NESTING edges recorded: `2`
- STAGE_ON_TORUS edge count: `32`

## 1. TopoNetX Candidate Cell-Complex View
- available: `False`
- error: `TopoNetX not installed`

## 2. Stage–Torus Cycle Groupings
- fiber stages (inner+clifford): `8`
- base stages (outer+clifford): `8`
- all admitted stages attach to Clifford: `True`
- Clifford is universal bridge in current owner scaffold: `True`
- `inner`: 8 stages
- `clifford`: 16 stages
- `outer`: 8 stages

## Runtime Bridge Alignment
- status: `present`
- runtime_bridge_json: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json`
- owner_content_hash_matches_runtime_bridge: `False`
- runtime_sample_count: `2`
- axis0_surface_status: `read_only_control_plane_summary_only`
- axis0_runtime_sample_count: `2`
- axis0_direct_bridge_families: `['Xi_LR_direct_control']`
- axis0_history_window_bridge_families: `['Xi_hist_window_control']`
- axis0_history_window_sample_counts: `[32]`
- `qit::ENGINE::type1_left_weyl`: first_step=`qit::SUBCYCLE_STEP::type1_left_weyl_Se_b_Ti`, last_step=`qit::SUBCYCLE_STEP::type1_left_weyl_Ne_f_Fi`
- `qit::ENGINE::type2_right_weyl`: first_step=`qit::SUBCYCLE_STEP::type2_right_weyl_Se_f_Ti`, last_step=`qit::SUBCYCLE_STEP::type2_right_weyl_Si_b_Fi`

## 3. Chirality Coupling Candidate Mapping (Cl(3,0))
- available: `False`
- type1_left_weyl: `Fe/Ti dominant on base, ψ_L → U·ψ_L`
- type2_right_weyl: `Te/Fi dominant on base, ψ_R → U*·ψ_R`
- coupling: `complementary_dominance (flat owner edge, sidecar annotation only)`

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

