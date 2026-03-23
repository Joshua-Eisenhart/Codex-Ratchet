---
id: "A2_3::SOURCE_MAP_PASS::v3_to_v4_migration_skill::dc63a8130a8dd18b"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_to_v4_migration_skill
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_to_v4_migration_skill::dc63a8130a8dd18b`

## Description
V3-to-V4 graphification ingestor (101 lines). Migrates system_v3 state into the v4 graph format. Translates old A2 state structures into GraphNode/GraphEdge representations.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[v4_graph_builder_skill]]
- **RELATED_TO** → [[zip_subagent_skill_family]]

## Inward Relations
- [[a2_v3_to_v4_graphification_ingestor.py]] → **SOURCE_MAP_PASS**
- [[v3_ingest_graph_data]] → **RELATED_TO**
- [[a2_graph_refinery_skill]] → **RELATED_TO**
- [[memory_admission_guard_skill]] → **RELATED_TO**
- [[slice_compiler_skill_family]] → **RELATED_TO**
- [[registry_types_skill]] → **RELATED_TO**
- [[a2_persistent_brain_skill]] → **RELATED_TO**
- [[a1_rosetta_mapper_skill]] → **RELATED_TO**
- [[a1_distiller_skill]] → **RELATED_TO**
- [[doc_queue_generator_skill]] → **RELATED_TO**
- [[promotion_audit_skill]] → **RELATED_TO**
- [[contradiction_scan_skill]] → **RELATED_TO**
- [[mass_extraction_runner_skill]] → **RELATED_TO**
- [[a2_brain_refresh_skill]] → **RELATED_TO**
- [[high_entropy_intake_skill]] → **RELATED_TO**
- [[a2_understanding_module]] → **RELATED_TO**
