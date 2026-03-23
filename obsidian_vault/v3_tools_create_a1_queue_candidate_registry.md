---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_create_a1_queue_candidate_registry::6994544b0dda2185"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_create_a1_queue_candidate_registry
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_create_a1_queue_candidate_registry::6994544b0dda2185`

## Description
create_a1_queue_candidate_registry.py (2184B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from validate_a1_queue_candidate_registry import validate as validate_registry   def _require_abs_existing(path_str: str, key:

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **EXCLUDES** → [[validate_a1_queue_candidate_registry_py]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
- [[a2_state_v3_a1_queue_candidate_registry__current__20]] → **EXCLUDES**
- [[test_a1_queue_candidate_registry_py]] → **EXCLUDES**
- [[a1_queue_candidate_registry_v1__pydantic_schema__2]] → **EXCLUDES**
- [[a1_queue_candidate_registry__current__2026_03_15__]] → **EXCLUDES**
- [[a1_queue_candidate_registry__substrate_base_scaffo]] → **EXCLUDES**
