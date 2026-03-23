---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_stage2_schema_gate::513937694f584fa0"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_stage2_schema_gate
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_stage2_schema_gate::513937694f584fa0`

## Description
stage2_schema_gate.py (7696B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import re from pathlib import Path from typing import Any   def _load_json(path: Path) -> Any:     return json.loads(path.read_text(encoding="utf-8"))   def _type_

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[run_codex_browser_launch_from_capture_record.py]] → **SOURCE_MAP_PASS**
