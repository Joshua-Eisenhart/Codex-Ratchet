---
id: "A2_3::SOURCE_MAP_PASS::a2_graph_refinery_skill::b1de7fdc066d4670"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# a2_graph_refinery_skill
**Node ID:** `A2_3::SOURCE_MAP_PASS::a2_graph_refinery_skill::b1de7fdc066d4670`

## Description
The A2 Graph Refinery itself (978 lines). Core engine: 3-layer refinery (A2-3 intake, A2-2 candidate, A2-1 kernel), session management, batch creation, doc queue, auto_extract prompt templates, process_extracted bridge, promote_node/demote_node/graph_audit methods. Classes: RefineryLayer, ExtractionMode, RefineryBatch. The central skill that orchestrates all knowledge ingestion and graph construction.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[a2_refinery_graph_data]]
- **RELATED_TO** → [[v3_ingest_graph_data]]
- **RELATED_TO** → [[v4_graph_builder_skill]]
- **RELATED_TO** → [[memory_admission_guard_skill]]
- **RELATED_TO** → [[slice_compiler_skill_family]]
- **RELATED_TO** → [[zip_subagent_skill_family]]
- **RELATED_TO** → [[registry_types_skill]]
- **RELATED_TO** → [[a2_persistent_brain_skill]]
- **RELATED_TO** → [[doc_queue_generator_skill]]
- **RELATED_TO** → [[promotion_audit_skill]]
- **RELATED_TO** → [[contradiction_scan_skill]]
- **RELATED_TO** → [[mass_extraction_runner_skill]]
- **RELATED_TO** → [[high_entropy_intake_skill]]
- **RELATED_TO** → [[v3_to_v4_migration_skill]]
- **RELATED_TO** → [[a2_understanding_module]]
- **DEPENDS_ON** → [[skill]]
- **DEPENDS_ON** → [[prompt-templates]]
- **DEPENDS_ON** → [[session]]

## Inward Relations
- [[a2_graph_refinery.py]] → **SOURCE_MAP_PASS**
- [[a1_rosetta_mapper_skill]] → **RELATED_TO**
- [[a1_distiller_skill]] → **RELATED_TO**
- [[a2_brain_refresh_skill]] → **RELATED_TO**
