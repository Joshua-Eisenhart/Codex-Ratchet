---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_build_a1_autoratchet_controller_res::fe4eea8077a76371"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_build_a1_autoratchet_controller_res
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_build_a1_autoratchet_controller_res::fe4eea8077a76371`

## Description
build_a1_autoratchet_controller_result.py (7592B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   def _read_json(path: Path) -> dict:     if not path.exists():         return {}     try:         data = json.loads(path.read_

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[browser_go_on_helper.py]] → **SOURCE_MAP_PASS**
