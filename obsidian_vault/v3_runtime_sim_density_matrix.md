---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_sim_density_matrix::cf58e8e202c447cd"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_sim_density_matrix
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_sim_density_matrix::cf58e8e202c447cd`

## Description
sim_density_matrix.py (1283B): import sys from pathlib import Path  RUNTIME_ROOT = Path(__file__).resolve().parents[1] if str(RUNTIME_ROOT) not in sys.path:     sys.path.insert(0, str(RUNTIME_ROOT)) from runtime_surface_guard import enforce_canonical_runtime  enforce_canonical_run

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[sim_decoherence.py]] → **SOURCE_MAP_PASS**
- [[generate_density_matrix_packet_py]] → **EXCLUDES**
- [[sim_density_matrix_py]] → **EXCLUDES**
- [[v3_runtime_generate_density_matrix_packet]] → **STRUCTURALLY_RELATED**
