---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_spec_lock_gate::fa817dec7b90b238"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_spec_lock_gate
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_spec_lock_gate::fa817dec7b90b238`

## Description
run_spec_lock_gate.py (2836B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import subprocess from pathlib import Path   def _write_json(path: Path, obj: dict) -> None:     path.parent.mkdir(parents=True, exist_ok=True)     path.write_text

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[run_codex_browser_launch_from_capture_record.py]] → **SOURCE_MAP_PASS**
