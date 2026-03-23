---
id: "A2_3::SOURCE_MAP_PASS::memory_admission_guard_skill::ae43c290ff9a99d6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# memory_admission_guard_skill
**Node ID:** `A2_3::SOURCE_MAP_PASS::memory_admission_guard_skill::ae43c290ff9a99d6`

## Description
Memory admission guard (224 lines). Detects FAKE_CANON labels, NARRATIVE_SMOOTHING signals, and enforces LAYER_WRITE_PERMISSIONS. Gate that prevents unauthorized writes to higher layers. Returns AdmissionResult (pass/fail + reasons).

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[v4_graph_builder_skill]]
- **RELATED_TO** → [[slice_compiler_skill_family]]
- **RELATED_TO** → [[zip_subagent_skill_family]]
- **RELATED_TO** → [[registry_types_skill]]
- **RELATED_TO** → [[promotion_audit_skill]]
- **RELATED_TO** → [[v3_to_v4_migration_skill]]
- **DEPENDS_ON** → [[events]]
- **EXCLUDES** → [[surface_class_and_memory_admission_rules__v1]]

## Inward Relations
- [[memory_admission_guard.py]] → **SOURCE_MAP_PASS**
- [[a2_graph_refinery_skill]] → **RELATED_TO**
- [[a2_persistent_brain_skill]] → **RELATED_TO**
- [[a1_rosetta_mapper_skill]] → **RELATED_TO**
- [[a1_distiller_skill]] → **RELATED_TO**
- [[doc_queue_generator_skill]] → **RELATED_TO**
- [[contradiction_scan_skill]] → **RELATED_TO**
- [[mass_extraction_runner_skill]] → **RELATED_TO**
- [[a2_brain_refresh_skill]] → **RELATED_TO**
- [[high_entropy_intake_skill]] → **RELATED_TO**
- [[a2_understanding_module]] → **RELATED_TO**
- [[a2_state_v3_surface_class_and_memory_admission_rules]] → **EXCLUDES**
