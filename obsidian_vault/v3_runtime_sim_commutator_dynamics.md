---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_sim_commutator_dynamics::f74633b866775e06"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_sim_commutator_dynamics
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_sim_commutator_dynamics::f74633b866775e06`

## Description
sim_commutator_dynamics.py (1354B): import sys from pathlib import Path  RUNTIME_ROOT = Path(__file__).resolve().parents[1] if str(RUNTIME_ROOT) not in sys.path:     sys.path.insert(0, str(RUNTIME_ROOT)) from runtime_surface_guard import enforce_canonical_runtime  enforce_canonical_run

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[dynamic]]

## Inward Relations
- [[a0_generator_v2.py]] → **SOURCE_MAP_PASS**
- [[sim_commutator_dynamics_py]] → **EXCLUDES**
