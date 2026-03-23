---
id: "A2_3::SOURCE_MAP_PASS::end_to_end_loop::473551f69d28de14"
type: "KERNEL_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "CROSS_VALIDATED"
---

# end_to_end_loop
**Node ID:** `A2_3::SOURCE_MAP_PASS::end_to_end_loop::473551f69d28de14`

## Description
Explicit 9-step processing loop: A2 Context -> A1 Strategy -> A0 Compile -> B Adjudicate -> A0 Snapshot -> A0 SIM Dispatch -> SIM Exec -> B SIM Ingest -> A1/A2 Feedback.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 2 sources, 2 batches, 8 edges
- **promoted_from**: A2_3_INTAKE

## Inward Relations
- [[08_PIPELINE_AND_STATE_FLOW_SPEC.md]] → **SOURCE_MAP_PASS**
- [[08_PIPELINE_AND_STATE_FLOW_SPEC.md]] → **OVERLAPS**
- [[V4_Pipeline_Components_Exist]] → **RELATED_TO**
- [[ZIP_PROTOCOL_V2_EIGHT_TYPE_SYSTEM]] → **RELATED_TO**
- [[BIDIRECTIONAL_LOOP_EVERY_STEP]] → **RELATED_TO**
- [[FIVE_LAYER_PIPELINE_A2_A1_A0_B_SIM]] → **RELATED_TO**
- [[end_to_end_9_step_loop]] → **RELATED_TO**
- [[v3_spec_08_pipeline_and_state_flow_spec]] → **DEPENDS_ON**
- [[sysrepair_v2_08_pipeline_and_state_flow_spe]] → **DEPENDS_ON**
- [[sysrepair_v3_08_pipeline_and_state_flow_spe]] → **DEPENDS_ON**
- [[sysrepair_v4_08_pipeline_and_state_flow_spe]] → **DEPENDS_ON**
