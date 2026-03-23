---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_sim_spec_bind_fixture::ee67090435f06598"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_sim_spec_bind_fixture
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_sim_spec_bind_fixture::ee67090435f06598`

## Description
test_sim_spec_bind_fixture.py (1082B): import sys from pathlib import Path  RUNTIME_ROOT = Path(__file__).resolve().parents[1] if str(RUNTIME_ROOT) not in sys.path:     sys.path.insert(0, str(RUNTIME_ROOT)) from runtime_surface_guard import enforce_canonical_runtime  enforce_canonical_run

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[zip_protocol_v2_writer.py]] → **SOURCE_MAP_PASS**
- [[test_sim_spec_bind_fixture_py]] → **EXCLUDES**
