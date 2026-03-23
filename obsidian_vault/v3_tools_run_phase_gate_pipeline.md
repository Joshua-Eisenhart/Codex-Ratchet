---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_phase_gate_pipeline::8c237df474357562"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_phase_gate_pipeline
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_phase_gate_pipeline::8c237df474357562`

## Description
run_phase_gate_pipeline.py (8873B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import subprocess from pathlib import Path   def _write_json(path: Path, obj: dict) -> None:     path.parent.mkdir(parents=True, exist_ok=True)     path.write_text

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[run_codex_browser_launch_from_capture_record.py]] → **SOURCE_MAP_PASS**
- [[eight_phase_gate_pipeline]] → **STRUCTURALLY_RELATED**
- [[run_phase_gate_pipeline_py]] → **STRUCTURALLY_RELATED**
- [[eight_phase_gate_pipeline]] → **STRUCTURALLY_RELATED**
- [[run_phase_gate_pipeline]] → **STRUCTURALLY_RELATED**
