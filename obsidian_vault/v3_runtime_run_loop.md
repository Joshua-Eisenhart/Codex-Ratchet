---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_run_loop::6fa51762c833513c"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_run_loop
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_run_loop::6fa51762c833513c`

## Description
run_loop.py (3129B): import argparse import hashlib import json import sys from pathlib import Path  RUNTIME_ROOT = Path(__file__).resolve().parents[1] if str(RUNTIME_ROOT) not in sys.path:     sys.path.insert(0, str(RUNTIME_ROOT)) from runtime_surface_guard import enfor

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[zip_protocol_v2_writer.py]] → **SOURCE_MAP_PASS**
