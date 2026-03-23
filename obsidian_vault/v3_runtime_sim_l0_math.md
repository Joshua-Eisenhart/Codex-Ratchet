---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_sim_l0_math::f902505ea5f49d9d"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_sim_l0_math
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_sim_l0_math::f902505ea5f49d9d`

## Description
sim_l0_math.py (519B): import sys from pathlib import Path  RUNTIME_ROOT = Path(__file__).resolve().parents[1] if str(RUNTIME_ROOT) not in sys.path:     sys.path.insert(0, str(RUNTIME_ROOT)) from runtime_surface_guard import enforce_canonical_runtime  enforce_canonical_run

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[sim_decoherence.py]] → **SOURCE_MAP_PASS**
