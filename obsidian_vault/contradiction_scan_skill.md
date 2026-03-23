---
id: "A2_3::SOURCE_MAP_PASS::contradiction_scan_skill::3696d74f233ac972"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# contradiction_scan_skill
**Node ID:** `A2_3::SOURCE_MAP_PASS::contradiction_scan_skill::3696d74f233ac972`

## Description
Contradiction scanner (240 lines). Detects name collisions, authority conflicts (CANON vs NONCANON), description duplicates, and edge contradictions across A2-2/A2-1 concepts. Outputs contradiction report. 4 detector functions with configurable similarity thresholds.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[v4_graph_builder_skill]]
- **RELATED_TO** → [[memory_admission_guard_skill]]
- **RELATED_TO** → [[slice_compiler_skill_family]]
- **RELATED_TO** → [[zip_subagent_skill_family]]
- **RELATED_TO** → [[registry_types_skill]]
- **RELATED_TO** → [[doc_queue_generator_skill]]
- **RELATED_TO** → [[promotion_audit_skill]]
- **RELATED_TO** → [[mass_extraction_runner_skill]]
- **RELATED_TO** → [[high_entropy_intake_skill]]
- **RELATED_TO** → [[v3_to_v4_migration_skill]]
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[functions]]
- **DEPENDS_ON** → [[function]]

## Inward Relations
- [[run_contradiction_scan.py]] → **SOURCE_MAP_PASS**
- [[contradiction_scan_report_2026_03_18]] → **RELATED_TO**
- [[a2_graph_refinery_skill]] → **RELATED_TO**
- [[a2_persistent_brain_skill]] → **RELATED_TO**
- [[a1_rosetta_mapper_skill]] → **RELATED_TO**
- [[a1_distiller_skill]] → **RELATED_TO**
- [[a2_brain_refresh_skill]] → **RELATED_TO**
- [[a2_understanding_module]] → **RELATED_TO**
