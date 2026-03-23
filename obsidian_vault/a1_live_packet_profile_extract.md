---
id: "A2_3::SOURCE_MAP_PASS::a1_live_packet_profile_extract::32b168b9fdd3340c"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "DRAFT"
---

# a1_live_packet_profile_extract
**Node ID:** `A2_3::SOURCE_MAP_PASS::a1_live_packet_profile_extract::32b168b9fdd3340c`

## Description
Current live A1 strategy: A1_STRATEGY_v1 object with schema, strategy_id, inputs, budget, policy, targets, alternatives, sims, self_audit. 7 live operators: OP_A1_GENERATED, OP_BIND_SIM, OP_REPAIR_DEF_FIELD, OP_MUTATE_LEXEME, OP_REORDER_DEPENDENCIES, OP_NEG_SIM_EXPAND, OP_INJECT_PROBE. Candidate shape: item_class, id, kind, requires[], def_fields[], asserts[], operator_id. Strict packet: extra root keys are fail-closed. Free English must not leak into kernel-lane compile fields.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[current]]
- **DEPENDS_ON** → [[a1_strategy_v1]]
- **DEPENDS_ON** → [[input]]
- **DEPENDS_ON** → [[object]]
- **DEPENDS_ON** → [[packet]]
- **EXCLUDES** → [[a2_state_v3_a2_update_note__a1_live_packet_profile_e]]
- **EXCLUDES** → [[v3_spec_77_a1_live_packet_profile_extract__]]
- **EXCLUDES** → [[a2_update_note__a1_live_packet_profile_extract__20]]

## Inward Relations
- [[77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md]] → **SOURCE_MAP_PASS**
- [[a2_state_v3_a1_worker_launch_gate_result__first_disp]] → **DEPENDS_ON**
- [[a2_state_v3_a1_worker_launch_handoff__first_dispatch]] → **DEPENDS_ON**
- [[a2_state_v3_a2_update_note__a1_live_packet_profile_e]] → **DEPENDS_ON**
- [[v3_spec_77_a1_live_packet_profile_extract__]] → **DEPENDS_ON**
- [[a1_worker_launch_packet__substrate_base_scaffold__]] → **DEPENDS_ON**
- [[a1_queue_status_packet__substrate_base_scaffold__b]] → **DEPENDS_ON**
- [[a1_worker_launch_gate_result__substrate_base_scaff]] → **DEPENDS_ON**
- [[a1_queue_status_packet__current_selector_registry_]] → **DEPENDS_ON**
- [[a1_worker_launch_packet__promoted_slice_verify__20]] → **DEPENDS_ON**
- [[a1_queue_status_packet__substrate_base_scaffold__2]] → **DEPENDS_ON**
- [[a1_queue_status_packet__current_ready_substrate__2]] → **DEPENDS_ON**
- [[a1_queue_status_packet__substrate_base_scaffold__p]] → **DEPENDS_ON**
- [[a1_worker_launch_packet__a1_dispatch__current_sele]] → **DEPENDS_ON**
- [[a1_worker_launch_packet__a1_dispatch__queue_packet]] → **DEPENDS_ON**
- [[B_SURVIVOR_F173_LABEL_DEF]] → **ACCEPTED_FROM**
- [[B_PARKED_F163]] → **PARKED_FROM**
- [[B_PARKED_F164]] → **PARKED_FROM**
- [[B_PARKED_F175]] → **PARKED_FROM**
- [[B_PARKED_F176]] → **PARKED_FROM**
- [[B_PARKED_F161]] → **PARKED_FROM**
