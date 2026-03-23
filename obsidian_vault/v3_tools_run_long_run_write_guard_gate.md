---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_long_run_write_guard_gate::eb779dd304f8bfa6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_long_run_write_guard_gate
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_long_run_write_guard_gate::eb779dd304f8bfa6`

## Description
run_long_run_write_guard_gate.py (5876B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import re from pathlib import Path   SHARD_RE = re.compile(r"^(.+)\.(\d{3})\.jsonl$")   def _write_json(path: Path, obj: dict) -> None:     path.parent.mkdir(paren

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[run_codex_browser_launch_from_capture_record.py]] → **SOURCE_MAP_PASS**
- [[run_long_run_write_guard_gate_py]] → **STRUCTURALLY_RELATED**
