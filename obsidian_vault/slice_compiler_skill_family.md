---
id: "A2_3::SOURCE_MAP_PASS::slice_compiler_skill_family::4b4c581fc6091352"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# slice_compiler_skill_family
**Node ID:** `A2_3::SOURCE_MAP_PASS::slice_compiler_skill_family::4b4c581fc6091352`

## Description
Slice compiler family (3 files, ~243 lines total). SliceCompiler: compiles registry records into bounded slices. SliceManifest: manifest of slice members with reject records. SliceRequest: defines slice parameters (LineageMode, WitnessMode, SliceClass). Together they implement bounded knowledge extraction from the graph.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[v4_graph_builder_skill]]
- **RELATED_TO** → [[zip_subagent_skill_family]]
- **RELATED_TO** → [[v3_to_v4_migration_skill]]
- **DEPENDS_ON** → [[implement]]
- **DEPENDS_ON** → [[request]]

## Inward Relations
- [[slice_compiler.py]] → **SOURCE_MAP_PASS**
- [[doc_queue_state]] → **RELATED_TO**
- [[a2_graph_refinery_skill]] → **RELATED_TO**
- [[memory_admission_guard_skill]] → **RELATED_TO**
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
