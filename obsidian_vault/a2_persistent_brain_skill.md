---
id: "A2_3::SOURCE_MAP_PASS::a2_persistent_brain_skill::489a9f91a1cf0bdf"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# a2_persistent_brain_skill
**Node ID:** `A2_3::SOURCE_MAP_PASS::a2_persistent_brain_skill::489a9f91a1cf0bdf`

## Description
A2 persistent brain (131 lines). A2PersistentBrain class: manages persistent A2-layer state across sessions. Loads/saves brain state, tracks context, maintains working memory between thread restarts.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[persistent_memory_state]]
- **RELATED_TO** → [[doc_queue_state]]
- **RELATED_TO** → [[refinery_batch_index_data]]
- **RELATED_TO** → [[rosetta_translation_state]]
- **RELATED_TO** → [[a2_proposal_state]]
- **RELATED_TO** → [[v4_graph_builder_skill]]
- **RELATED_TO** → [[memory_admission_guard_skill]]
- **RELATED_TO** → [[slice_compiler_skill_family]]
- **RELATED_TO** → [[zip_subagent_skill_family]]
- **RELATED_TO** → [[registry_types_skill]]
- **RELATED_TO** → [[doc_queue_generator_skill]]
- **RELATED_TO** → [[promotion_audit_skill]]
- **RELATED_TO** → [[contradiction_scan_skill]]
- **RELATED_TO** → [[mass_extraction_runner_skill]]
- **RELATED_TO** → [[high_entropy_intake_skill]]
- **RELATED_TO** → [[v3_to_v4_migration_skill]]
- **RELATED_TO** → [[a2_understanding_module]]
- **DEPENDS_ON** → [[a2_persistent_brain]]
- **DEPENDS_ON** → [[start]]
- **DEPENDS_ON** → [[session]]

## Inward Relations
- [[a2_persistent_brain.py]] → **SOURCE_MAP_PASS**
- [[a2_graph_refinery_skill]] → **RELATED_TO**
- [[a1_rosetta_mapper_skill]] → **RELATED_TO**
- [[a1_distiller_skill]] → **RELATED_TO**
- [[a2_brain_refresh_skill]] → **RELATED_TO**
