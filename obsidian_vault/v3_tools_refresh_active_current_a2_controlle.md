---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_refresh_active_current_a2_controlle::6ea5dc675c78c4b6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_refresh_active_current_a2_controlle
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_refresh_active_current_a2_controlle::6ea5dc675c78c4b6`

## Description
refresh_active_current_a2_controller_launch_spine.py (5695B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import subprocess import sys from pathlib import Path   def _repo_root() -> Path:     return Path(__file__).resolve().parents[2]   def _default_packet_json() -> Pa

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[current]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[extract_parallel_codex_worker_result.py]] → **SOURCE_MAP_PASS**
