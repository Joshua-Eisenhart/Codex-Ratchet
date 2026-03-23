---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_prepare_current_a1_queue_status_fro::665b2a82f371a14e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_prepare_current_a1_queue_status_fro
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_prepare_current_a1_queue_status_fro::665b2a82f371a14e`

## Description
prepare_current_a1_queue_status_from_candidates.py (7901B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import subprocess import sys from pathlib import Path   def _require_abs_path(path_str: str, key: str) -> Path:     path = Path(path_str)     if not path.is_absolu

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[current]]

## Inward Relations
- [[extract_parallel_codex_worker_result.py]] → **SOURCE_MAP_PASS**
