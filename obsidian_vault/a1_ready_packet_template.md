---
id: "A2_3::SOURCE_MAP_PASS::a1_ready_packet_template::bf41dfeeb5a22888"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "DRAFT"
---

# a1_ready_packet_template
**Node ID:** `A2_3::SOURCE_MAP_PASS::a1_ready_packet_template::bf41dfeeb5a22888`

## Description
Minimal current A1_READY_PACKET requires: model, thread_class (A1_WORKER), mode (PROPOSAL_ONLY), dispatch_id, queue_status, target_a1_role, required_a1_boot, a1_reload_artifacts, source_a2_artifacts, bounded_scope, prompt_to_send, stop_rule, go_on_count, go_on_budget. Includes role-specific prompt skeletons for A1_ROSETTA, A1_PROPOSAL, A1_PACKAGING. Prompt must not refer to hidden context or old threads.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[current]]
- **DEPENDS_ON** → [[packaging]]
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[34_A1_READY_PACKET__v1.md]] → **SOURCE_MAP_PASS**
