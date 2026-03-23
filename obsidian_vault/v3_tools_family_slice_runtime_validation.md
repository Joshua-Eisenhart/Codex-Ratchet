---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_family_slice_runtime_validation::c774a9fa060ad3a4"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_family_slice_runtime_validation
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_family_slice_runtime_validation::c774a9fa060ad3a4`

## Description
family_slice_runtime_validation.py (739B): #!/usr/bin/env python3 from __future__ import annotations  import sys from pathlib import Path from typing import Any   def _repo_root() -> Path:     return Path(__file__).resolve().parents[2]   def _planner_tools_root() -> Path:     return _repo_roo

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[planner]]

## Inward Relations
- [[extract_parallel_codex_worker_result.py]] → **SOURCE_MAP_PASS**
