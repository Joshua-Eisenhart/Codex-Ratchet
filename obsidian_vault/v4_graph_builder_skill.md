---
id: "A2_3::SOURCE_MAP_PASS::v4_graph_builder_skill::c6089426204fb13b"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v4_graph_builder_skill
**Node ID:** `A2_3::SOURCE_MAP_PASS::v4_graph_builder_skill::c6089426204fb13b`

## Description
V4 System Graph builder (134 lines). Pydantic models: GraphNode (id, node_type, layer, name, description, properties, trust_zone, admissibility_state), GraphEdge (source_id, target_id, relation, attributes), V4SystemGraph (nodes dict, edges list). The data layer beneath the refinery.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[zip_subagent_skill_family]]
- **DEPENDS_ON** → [[models]]

## Inward Relations
- [[v4_graph_builder.py]] → **SOURCE_MAP_PASS**
- [[registry_types_skill]] → **RELATED_TO**
- [[a2_graph_refinery_skill]] → **RELATED_TO**
- [[memory_admission_guard_skill]] → **RELATED_TO**
- [[slice_compiler_skill_family]] → **RELATED_TO**
- [[a2_persistent_brain_skill]] → **RELATED_TO**
- [[a1_rosetta_mapper_skill]] → **RELATED_TO**
- [[a1_distiller_skill]] → **RELATED_TO**
- [[doc_queue_generator_skill]] → **RELATED_TO**
- [[promotion_audit_skill]] → **RELATED_TO**
- [[contradiction_scan_skill]] → **RELATED_TO**
- [[mass_extraction_runner_skill]] → **RELATED_TO**
- [[a2_brain_refresh_skill]] → **RELATED_TO**
- [[high_entropy_intake_skill]] → **RELATED_TO**
- [[v3_to_v4_migration_skill]] → **RELATED_TO**
- [[a2_understanding_module]] → **RELATED_TO**
