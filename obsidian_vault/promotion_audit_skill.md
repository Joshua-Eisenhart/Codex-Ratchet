---
id: "A2_3::SOURCE_MAP_PASS::promotion_audit_skill::0304bc175eb97392"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# promotion_audit_skill
**Node ID:** `A2_3::SOURCE_MAP_PASS::promotion_audit_skill::0304bc175eb97392`

## Description
Promotion audit runner (220 lines). Scans A2-2 candidates, applies 4 deterministic gates (G1 source coverage, G2 cross-reference density, G3 authority check, G4 contradiction absence), scores and ranks candidates for A2-1 kernel promotion. Outputs audit report to audit_logs/.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[promotion_binding_and_evidence_digests]]
- **RELATED_TO** → [[v4_graph_builder_skill]]
- **RELATED_TO** → [[slice_compiler_skill_family]]
- **RELATED_TO** → [[zip_subagent_skill_family]]
- **RELATED_TO** → [[registry_types_skill]]
- **RELATED_TO** → [[v3_to_v4_migration_skill]]
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[reference]]

## Inward Relations
- [[run_promotion_audit.py]] → **SOURCE_MAP_PASS**
- [[promotion_audit_report_2026_03_18]] → **RELATED_TO**
- [[eleven_conformance_gates]] → **RELATED_TO**
- [[promotion_audit_package]] → **RELATED_TO**
- [[contradiction_scan_report_2026_03_18]] → **RELATED_TO**
- [[a2_graph_refinery_skill]] → **RELATED_TO**
- [[memory_admission_guard_skill]] → **RELATED_TO**
- [[a2_persistent_brain_skill]] → **RELATED_TO**
- [[a1_rosetta_mapper_skill]] → **RELATED_TO**
- [[a1_distiller_skill]] → **RELATED_TO**
- [[doc_queue_generator_skill]] → **RELATED_TO**
- [[contradiction_scan_skill]] → **RELATED_TO**
- [[mass_extraction_runner_skill]] → **RELATED_TO**
- [[a2_brain_refresh_skill]] → **RELATED_TO**
- [[high_entropy_intake_skill]] → **RELATED_TO**
- [[a2_understanding_module]] → **RELATED_TO**
