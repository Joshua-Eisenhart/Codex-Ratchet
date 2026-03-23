---
id: "A2_3::SOURCE_MAP_PASS::run_surface_scaffolding::7e235fd9869eee51"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# run_surface_scaffolding
**Node ID:** `A2_3::SOURCE_MAP_PASS::run_surface_scaffolding::7e235fd9869eee51`

## Description
Deterministic scaffolding for implementation/test runs from (run_id, baseline_state_hash, strategy_hash, spec_hash, bootpack_b_hash, bootpack_a_hash). Emits identical file tree/contents for identical inputs. Fails closed if target dir exists and is non-empty.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md]] → **SOURCE_MAP_PASS**
- [[run_surface_scaffolder_determinism]] → **DEPENDS_ON**
- [[v3_spec_22_run_surface_template_and_scaffol]] → **DEPENDS_ON**
- [[sysrepair_v2_22_run_surface_template_and_sc]] → **DEPENDS_ON**
- [[sysrepair_v3_22_run_surface_template_and_sc]] → **DEPENDS_ON**
- [[sysrepair_v4_22_run_surface_template_and_sc]] → **DEPENDS_ON**
