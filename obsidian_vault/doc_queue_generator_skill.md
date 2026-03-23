---
id: "A2_3::SOURCE_MAP_PASS::doc_queue_generator_skill::2a3873071e30ce73"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# doc_queue_generator_skill
**Node ID:** `A2_3::SOURCE_MAP_PASS::doc_queue_generator_skill::2a3873071e30ce73`

## Description
Document queue generator (242 lines). Scans workspace, classifies files by entropy class (SPEC_CORE, SPEC_SUPPLEMENT, CONTROL_PLANE, etc.), sorts by processing priority (MD first, then by entropy order), generates doc_queue.json. The intake surface for the refinery.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[high_entropy_intake_skill]]
- **RELATED_TO** → [[v4_graph_builder_skill]]
- **RELATED_TO** → [[memory_admission_guard_skill]]
- **RELATED_TO** → [[slice_compiler_skill_family]]
- **RELATED_TO** → [[zip_subagent_skill_family]]
- **RELATED_TO** → [[registry_types_skill]]
- **RELATED_TO** → [[promotion_audit_skill]]
- **RELATED_TO** → [[mass_extraction_runner_skill]]
- **RELATED_TO** → [[v3_to_v4_migration_skill]]
- **RELATED_TO** → [[doc_queue_state]]
- **DEPENDS_ON** → [[generator]]

## Inward Relations
- [[generate_doc_queue.py]] → **SOURCE_MAP_PASS**
- [[a2_graph_refinery_skill]] → **RELATED_TO**
- [[a2_persistent_brain_skill]] → **RELATED_TO**
- [[a1_rosetta_mapper_skill]] → **RELATED_TO**
- [[a1_distiller_skill]] → **RELATED_TO**
- [[contradiction_scan_skill]] → **RELATED_TO**
- [[a2_brain_refresh_skill]] → **RELATED_TO**
- [[a2_understanding_module]] → **RELATED_TO**
