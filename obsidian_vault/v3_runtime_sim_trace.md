---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_sim_trace::6c20bfe474c88f91"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_sim_trace
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_sim_trace::6c20bfe474c88f91`

## Description
sim_trace.py (1018B): import sys from pathlib import Path  RUNTIME_ROOT = Path(__file__).resolve().parents[1] if str(RUNTIME_ROOT) not in sys.path:     sys.path.insert(0, str(RUNTIME_ROOT)) from runtime_surface_guard import enforce_canonical_runtime  enforce_canonical_run

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[sim_term_generic_negative.py]] → **SOURCE_MAP_PASS**
