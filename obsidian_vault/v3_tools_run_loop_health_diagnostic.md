---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_loop_health_diagnostic::1cea8064cbdc12e6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_loop_health_diagnostic
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_loop_health_diagnostic::1cea8064cbdc12e6`

## Description
run_loop_health_diagnostic.py (3502B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from collections import Counter from pathlib import Path   def _write_json(path: Path, obj: dict) -> None:     path.parent.mkdir(parents=True, exist_ok=True)     p

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[run_codex_browser_launch_from_capture_record.py]] → **SOURCE_MAP_PASS**
- [[run_loop_health_diagnostic_py]] → **EXCLUDES**
