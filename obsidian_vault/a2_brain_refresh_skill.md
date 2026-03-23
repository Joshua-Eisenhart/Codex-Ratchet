---
id: "A2_3::SOURCE_MAP_PASS::a2_brain_refresh_skill::dd5b8efbb36a2432"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# a2_brain_refresh_skill
**Node ID:** `A2_3::SOURCE_MAP_PASS::a2_brain_refresh_skill::dd5b8efbb36a2432`

## Description
A2 brain refresh (239 lines). Refreshes A2 brain state: reloads context, updates working memory, synchronizes with graph state. Called at session start to ensure A2 has current awareness.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[a2_graph_refinery_skill]]
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
- **DEPENDS_ON** → [[current]]
- **DEPENDS_ON** → [[start]]
- **DEPENDS_ON** → [[session]]

## Inward Relations
- [[a2_brain_refresh.py]] → **SOURCE_MAP_PASS**
- [[a1_rosetta_mapper_skill]] → **RELATED_TO**
- [[a1_distiller_skill]] → **RELATED_TO**
