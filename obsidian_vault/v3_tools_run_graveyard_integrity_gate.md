---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_graveyard_integrity_gate::855b234e8089f93f"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_graveyard_integrity_gate
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_graveyard_integrity_gate::855b234e8089f93f`

## Description
run_graveyard_integrity_gate.py (4194B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path   def _write_json(path: Path, obj: dict) -> None:     path.parent.mkdir(parents=True, exist_ok=True)     path.write_text(json.dumps(obj, i

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[run_codex_browser_launch_from_capture_record.py]] → **SOURCE_MAP_PASS**
