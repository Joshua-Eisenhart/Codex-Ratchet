---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_fuel_cursor::1a68b6f97b0b5c8b"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_fuel_cursor
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_fuel_cursor::1a68b6f97b0b5c8b`

## Description
fuel_cursor.py (881B): import sys from pathlib import Path  RUNTIME_ROOT = Path(__file__).resolve().parents[1] if str(RUNTIME_ROOT) not in sys.path:     sys.path.insert(0, str(RUNTIME_ROOT)) from runtime_surface_guard import enforce_canonical_runtime  enforce_canonical_run

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[a0_generator_v2.py]] → **SOURCE_MAP_PASS**
