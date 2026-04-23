# GRAPH_CAPABILITY_AUDIT__CURRENT__v1

generated_utc: 2026-03-22T02:55:39Z
authoritative_live_store: /home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/graphs/system_graph_a2_refinery.json
authoritative_node_count: 19939
authoritative_edge_count: 40643
canonical_graph_count: 1
explicit_identity_registry: True
typed_layer_stores_materialized: 4
next_recommended_unit: None

## Current Queue Handoff
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

## Nested Queue Health
- queue_status: NO_WORK
- program_status: NO_CURRENT_WORK__DIRECT_ENTROPY_EXECUTABLE_PAUSED
- queue_handoff_state: NO_WORK
- observation_sync_state: in_sync
- observation_source: queue_packet
- stored_health_sync_state: in_sync
- stored_health_source: queue_packet
- stored_health_match_state: matches_observations
- preserved_overlap_health_derived_from: preserved_overlap_observation_summary
- preserved_overlap_health_observation_mode: non_operative
- preserved_overlap_health_layer_count: 3
- preserved_overlap_health_treatment_reported_layer_count: 2
- preserved_overlap_health_no_preserve_diagnostics_layer_count: 1
- preserved_overlap_health_preserved_only_overlap_layer_count: 2
- preserved_overlap_health_max_preserved_only_overlap_edge_count: 2947
- carryover_heavy_layer_count: 2
- carryover_heavy_layers: ['A2_MID_REFINEMENT', 'A2_LOW_CONTROL']
- observation_flags: ['queue_paused_no_work', 'program_paused_no_current_work', 'observation_sync_in_place', 'carryover_heavy_a2_layers_observed']

## Layer Population In Master Graph
- A0_COMPILED: 401
- A1_CARTRIDGE: 401
- A1_JARGONED: 420
- A1_STRIPPED: 401
- A2: 7
- A2_2_CANDIDATE: 1153
- A2_3_INTAKE: 4
- A2_HIGH_INTAKE: 5765
- A2_LOW_CONTROL: 9
- A2_MID_REFINEMENT: 170
- B_ADJUDICATED: 575
- GRAVEYARD: 324
- INDEX: 10099
- SIM_EVIDENCED: 67
- SKILL_REGISTRY: 123
- TERM_REGISTRY: 20

## Skill Graph Coverage
- active_skill_count: 123
- graphed_skill_node_count: 123
- matching_active_skill_count: 123
- missing_active_skill_count: 0
- stale_skill_node_count: 0
- isolated_skill_node_count: 0
- single_edge_skill_node_count: 35
- fully_graphed: True
- sample_single_edge_skill_ids: ['a0-compiler', 'a1-distiller', 'a1-from-a2-distillation', 'a1-rosetta-mapper', 'a1-routing-state', 'a2-graph-refinery', 'a2-thermodynamic-purge', 'automation-controller', 'b-adjudicator', 'brain-delta-consolidation']

## Target Layer Store Status
- A2_HIGH_INTAKE: MATERIALIZED (/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/graphs/a2_high_intake_graph_v1.json)
- A2_MID_REFINEMENT: MATERIALIZED (/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json)
- A2_LOW_CONTROL: MATERIALIZED (/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/graphs/a2_low_control_graph_v1.json)
- A1_JARGONED: MATERIALIZED (/home/ratchet/Desktop/Codex Ratchet/system_v4/a1_state/a1_jargoned_graph_v1.json)
- A1_STRIPPED: BLOCKED (/home/ratchet/Desktop/Codex Ratchet/system_v4/a1_state/a1_stripped_graph_v1.json)
- A1_CARTRIDGE: BLOCKED (/home/ratchet/Desktop/Codex Ratchet/system_v4/a1_state/a1_cartridge_graph_v1.json)

## Preserved Overlap Treatment
- A2_HIGH_INTAKE: state=no_preserve_diagnostics_present preserved_only_edges=0 preserved_only_overlaps=0
- A2_MID_REFINEMENT: state=treatment_reported preserved_only_edges=2953 preserved_only_overlaps=2947
  - current_runtime_effect: none_observed_in_live_consumers
  - equal_runtime_weight_admissible_now: False
  - recommended_future_handling: quarantine_or_downrank_before_equal_runtime_use
  - reason_flags: ['preserved_only_carryover_not_in_current_master_graph', 'overlap_dominant_carryover', 'overlap_attribute_contract_mismatch', 'no_direct_live_owner_edge_consumer_observed']
- A2_LOW_CONTROL: state=treatment_reported preserved_only_edges=620 preserved_only_overlaps=614
  - current_runtime_effect: none_observed_in_live_consumers
  - equal_runtime_weight_admissible_now: False
  - recommended_future_handling: quarantine_or_downrank_before_equal_runtime_use
  - reason_flags: ['preserved_only_carryover_not_in_current_master_graph', 'overlap_dominant_carryover', 'overlap_attribute_contract_mismatch', 'no_direct_live_owner_edge_consumer_observed']

## Query Capabilities
- nx_ancestors: available=True relation_filter=True
- nx_descendants: available=True relation_filter=True
- nx_ego_graph: available=True relation_filter=True
- nx_simple_cycles: available=True relation_filter=True
- nx_topological_sort: available=True relation_filter=True

## Current Limits
- one authoritative live graph store still carries all A2/A1 populations
- separate layer store blocked for A1_STRIPPED
- separate layer store blocked for A1_CARTRIDGE
- A1 graph projection has no explicit edge list
- nested_graph_v1 is a projection summary, not a live owner graph
- current queued correction flow is intentionally paused with no immediate bounded follow-on lane
- bridge contracts between the intended 3+3 layer stores are not materialized as separate owner surfaces
