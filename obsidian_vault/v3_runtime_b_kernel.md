---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_b_kernel::6383a795dbc4cad1"
type: "REFINED_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_b_kernel
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_b_kernel::6383a795dbc4cad1`

## Description
b_kernel.py (7254B): import sys from pathlib import Path  RUNTIME_ROOT = Path(__file__).resolve().parents[1] if str(RUNTIME_ROOT) not in sys.path:     sys.path.insert(0, str(RUNTIME_ROOT)) from runtime_surface_guard import enforce_canonical_runtime  enforce_canonical_run

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 2 sources, 2 batches, 2 edges
- **promoted_from**: A2_3_INTAKE

## Inward Relations
- [[zip_protocol_v2_writer.py]] → **SOURCE_MAP_PASS**
- [[a0_generator_v2.py]] → **OVERLAPS**
