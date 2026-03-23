---
id: "A2_3::SOURCE_MAP_PASS::a1_consolidation_prepack_job::1624c49dd9e2315f"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# a1_consolidation_prepack_job
**Node ID:** `A2_3::SOURCE_MAP_PASS::a1_consolidation_prepack_job::1624c49dd9e2315f`

## Description
Upper-layer DRAFT ZIP_JOB family. Merges multiple A1 worker outputs into one strict pre-A0 A1_STRATEGY_v1 candidate. Solves the many-worker exploratory richness issue.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[a1_strategy_v1]]
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[worker]]
- **EXCLUDES** → [[run_a1_consolidation_prepack_job_py]]

## Inward Relations
- [[A1_CONSOLIDATION_PREPACK_JOB__v1.md]] → **SOURCE_MAP_PASS**
- [[a1_strategy_schema_and_repair]] → **DEPENDS_ON**
- [[control_plane_readme]] → **DEPENDS_ON**
- [[control_plane_zip_job_manifest_v1]] → **DEPENDS_ON**
- [[control_plane_a1_consolidation_prepack_job__v1]] → **DEPENDS_ON**
- [[v3_tools_run_a1_consolidation_prepack_job]] → **DEPENDS_ON**
