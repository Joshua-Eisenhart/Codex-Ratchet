---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_refresh_active_current_a1_queue_sta::de6646c8ce60500a"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_refresh_active_current_a1_queue_sta
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_refresh_active_current_a1_queue_sta::de6646c8ce60500a`

## Description
refresh_active_current_a1_queue_state.py (7013B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import subprocess import sys from pathlib import Path   def _repo_root() -> Path:     return Path(__file__).resolve().parents[2]   def _default_candidate_registry(

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[current]]

## Inward Relations
- [[extract_parallel_codex_worker_result.py]] → **SOURCE_MAP_PASS**
