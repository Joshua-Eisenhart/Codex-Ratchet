---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_emit_a2_controller_launch_gate_resu::2cb08e667fddcb5e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_emit_a2_controller_launch_gate_resu
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_emit_a2_controller_launch_gate_resu::2cb08e667fddcb5e`

## Description
emit_a2_controller_launch_gate_result_pydantic_schema.py (1154B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from a2_controller_launch_gate_result_models import A2ControllerLaunchGateResult   def _write_json(path: Path, payload: dict) 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[emit_a2_controller_launch_gate_result_pydantic_sch]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
