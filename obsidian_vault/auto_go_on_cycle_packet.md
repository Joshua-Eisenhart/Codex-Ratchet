---
id: "A2_3::SOURCE_MAP_PASS::auto_go_on_cycle_packet::8d83c551e7e9af9d"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# auto_go_on_cycle_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::auto_go_on_cycle_packet::8d83c551e7e9af9d`

## Description
The one-shot execution input that maps raw thread text to the normalized runner cycle. Only points to absolute paths, never embedded text.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **EXCLUDES** → [[derived_indices_auto_go_on_cycle_packet_template_v1]]
- **EXCLUDES** → [[v3_spec_47_auto_go_on_cycle_packet__v1]]
- **EXCLUDES** → [[v3_tools_create_auto_go_on_cycle_packet]]
- **EXCLUDES** → [[v3_tools_run_auto_go_on_cycle]]
- **EXCLUDES** → [[v3_tools_run_auto_go_on_cycle_from_packet]]
- **EXCLUDES** → [[create_auto_go_on_cycle_packet_py]]
- **EXCLUDES** → [[run_auto_go_on_cycle_from_packet_py]]
- **EXCLUDES** → [[run_auto_go_on_cycle_py]]
- **EXCLUDES** → [[auto_go_on_cycle_packet_template_v1_json]]
- **DEPENDS_ON** → [[input]]

## Inward Relations
- [[47_AUTO_GO_ON_CYCLE_PACKET__v1.md]] → **SOURCE_MAP_PASS**
- [[derived_indices_auto_go_on_cycle_packet_template_v1]] → **DEPENDS_ON**
- [[v3_spec_47_auto_go_on_cycle_packet__v1]] → **DEPENDS_ON**
- [[v3_tools_run_auto_go_on_from_metadata]] → **DEPENDS_ON**
