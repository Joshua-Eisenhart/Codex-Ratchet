# NESTED_GRAPH_LAYER_AUDIT__CURRENT__v1

generated_utc: 2026-03-21T02:10:56Z
program_path: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/NESTED_GRAPH_BUILD_PROGRAM__2026_03_20__v1.json
program_status: NO_CURRENT_WORK__DIRECT_ENTROPY_EXECUTABLE_PAUSED
ready_unit_id: 
current_queue_status: NO_WORK
next_required_lane: 
live_substrate: single_authoritative_multigraph_plus_projections

## CURRENT_QUEUE_HANDOFF
- path: 
- unit_id: 
- dispatch_id: 
- layer_id: 
- role_type: 
- thread_class: 
- mode: 
- queue_status: NO_WORK
- state: NO_WORK
- existing_outputs: 0/0

## PRESERVED_OVERLAP_OBSERVATIONS
- A2_HIGH_INTAKE: state=no_preserve_diagnostics_present preserved_only_edges=0 preserved_only_overlaps=0
- A2_MID_REFINEMENT: state=treatment_reported preserved_only_edges=2953 preserved_only_overlaps=2947
  - current_runtime_effect: none_observed_in_live_consumers
  - reason_flags: ['preserved_only_carryover_not_in_current_master_graph', 'overlap_dominant_carryover', 'overlap_attribute_contract_mismatch', 'no_direct_live_owner_edge_consumer_observed']
- A2_LOW_CONTROL: state=treatment_reported preserved_only_edges=620 preserved_only_overlaps=614
  - current_runtime_effect: none_observed_in_live_consumers
  - reason_flags: ['preserved_only_carryover_not_in_current_master_graph', 'overlap_dominant_carryover', 'overlap_attribute_contract_mismatch', 'no_direct_live_owner_edge_consumer_observed']

## IDENTITY_REGISTRY
- unit_id: IDENTITY_REGISTRY
- dispatch_id: NESTED_GRAPH_BUILD__IDENTITY_REGISTRY__2026_03_20__v1
- declared_status: MATERIALIZED_FROM_EXISTING_FUEL
- current_state: MATERIALIZED
- owner_surface_state: MATERIALIZED
- owner_surface: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/identity_registry_v1.json
- existing_outputs: 3/3

## A2_HIGH_INTAKE
- unit_id: A2_HIGH_INTAKE
- dispatch_id: NESTED_GRAPH_BUILD__A2_HIGH_INTAKE__2026_03_20__v1
- declared_status: MATERIALIZED_FROM_EXISTING_FUEL
- current_state: MATERIALIZED
- owner_surface_state: MATERIALIZED
- owner_surface: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/a2_high_intake_graph_v1.json
- existing_outputs: 2/2

## A2_MID_REFINEMENT
- unit_id: A2_MID_REFINEMENT
- dispatch_id: NESTED_GRAPH_BUILD__A2_MID_REFINEMENT__2026_03_20__v1
- declared_status: MATERIALIZED_FROM_EXISTING_FUEL
- current_state: MATERIALIZED
- owner_surface_state: MATERIALIZED
- owner_surface: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json
- existing_outputs: 2/2

## A2_LOW_CONTROL
- unit_id: A2_LOW_CONTROL
- dispatch_id: NESTED_GRAPH_BUILD__A2_LOW_CONTROL__2026_03_20__v1
- declared_status: MATERIALIZED_FROM_EXISTING_FUEL
- current_state: MATERIALIZED
- owner_surface_state: MATERIALIZED
- owner_surface: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/a2_low_control_graph_v1.json
- existing_outputs: 2/2

## A1_JARGONED
- unit_id: A1_JARGONED
- dispatch_id: NESTED_GRAPH_BUILD__A1_JARGONED__2026_03_20__v1
- declared_status: MATERIALIZED_FROM_SCOPE_ALIGNED_FUEL
- current_state: MATERIALIZED
- owner_surface_state: MATERIALIZED
- owner_surface: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a1_state/a1_jargoned_graph_v1.json
- existing_outputs: 2/2

## A1_STRIPPED
- unit_id: A1_STRIPPED
- dispatch_id: NESTED_GRAPH_BUILD__A1_STRIPPED__2026_03_20__v1
- declared_status: BLOCKED_ON_DIRECT_ENTROPY_EXECUTABLE_PAUSE
- current_state: BLOCKED
- owner_surface_state: BLOCKED
- owner_surface: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a1_state/a1_stripped_graph_v1.json
- existing_outputs: 2/2

## A1_CARTRIDGE
- unit_id: A1_CARTRIDGE
- dispatch_id: NESTED_GRAPH_BUILD__A1_CARTRIDGE__2026_03_20__v1
- declared_status: BLOCKED_ON_DIRECT_ENTROPY_EXECUTABLE_PAUSE
- current_state: BLOCKED
- owner_surface_state: BLOCKED
- owner_surface: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a1_state/a1_cartridge_graph_v1.json
- existing_outputs: 2/2
