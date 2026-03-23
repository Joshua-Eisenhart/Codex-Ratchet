---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_replay_pair_gate::74717c6353eba1f6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_replay_pair_gate
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_replay_pair_gate::74717c6353eba1f6`

## Description
run_replay_pair_gate.py (5018B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path   def _read_json(path: Path) -> dict:     if not path.exists():         return {}     try:         return json.loads(path.read_text(encodi

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[run_codex_browser_launch_from_capture_record.py]] → **SOURCE_MAP_PASS**
- [[run_replay_pair_gate_py]] → **EXCLUDES**
