---
id: "A2_3::SOURCE_MAP_PASS::mass_extraction_runner_skill::2cc79c48836ae4fa"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# mass_extraction_runner_skill
**Node ID:** `A2_3::SOURCE_MAP_PASS::mass_extraction_runner_skill::2cc79c48836ae4fa`

## Description
Mass extraction runner (154 lines). Tier-based batch extraction runner. Processes doc queue in entropy order, batch-ingests documents by category. The main automation driver for the refinery pipeline.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[run_phase_gate_pipeline]]
- **RELATED_TO** → [[v4_graph_builder_skill]]
- **RELATED_TO** → [[memory_admission_guard_skill]]
- **RELATED_TO** → [[slice_compiler_skill_family]]
- **RELATED_TO** → [[zip_subagent_skill_family]]
- **RELATED_TO** → [[registry_types_skill]]
- **RELATED_TO** → [[promotion_audit_skill]]
- **RELATED_TO** → [[v3_to_v4_migration_skill]]

## Inward Relations
- [[run_mass_extraction.py]] → **SOURCE_MAP_PASS**
- [[browser_observed_packet_to_proof_path]] → **RELATED_TO**
- [[browser_observed_packet_to_playwright_proof_path]] → **RELATED_TO**
- [[auto_go_on_runner]] → **RELATED_TO**
- [[a2_graph_refinery_skill]] → **RELATED_TO**
- [[a2_persistent_brain_skill]] → **RELATED_TO**
- [[a1_rosetta_mapper_skill]] → **RELATED_TO**
- [[a1_distiller_skill]] → **RELATED_TO**
- [[doc_queue_generator_skill]] → **RELATED_TO**
- [[contradiction_scan_skill]] → **RELATED_TO**
- [[a2_brain_refresh_skill]] → **RELATED_TO**
- [[high_entropy_intake_skill]] → **RELATED_TO**
- [[a2_understanding_module]] → **RELATED_TO**
