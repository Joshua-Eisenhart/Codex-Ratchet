---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_sim_term_generic_negative::21665b65ee4fa43a"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_sim_term_generic_negative
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_sim_term_generic_negative::21665b65ee4fa43a`

## Description
sim_term_generic_negative.py (869B): import sys from pathlib import Path  RUNTIME_ROOT = Path(__file__).resolve().parents[1] if str(RUNTIME_ROOT) not in sys.path:     sys.path.insert(0, str(RUNTIME_ROOT)) from runtime_surface_guard import enforce_canonical_runtime  enforce_canonical_run

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[sim_term_generic_negative.py]] → **SOURCE_MAP_PASS**
- [[sim_term_generic_negative_py]] → **STRUCTURALLY_RELATED**
- [[v3_runtime_sim_math_generic_negative]] → **STRUCTURALLY_RELATED**
- [[sim_math_generic_negative_py]] → **STRUCTURALLY_RELATED**
- [[sim_term_generic_py]] → **EXCLUDES**
- [[v3_runtime_sim_term_generic]] → **STRUCTURALLY_RELATED**
