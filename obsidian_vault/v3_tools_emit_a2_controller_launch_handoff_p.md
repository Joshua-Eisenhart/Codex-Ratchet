---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_emit_a2_controller_launch_handoff_p::37325de22790fdb7"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_emit_a2_controller_launch_handoff_p
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_emit_a2_controller_launch_handoff_p::37325de22790fdb7`

## Description
emit_a2_controller_launch_handoff_pydantic_schema.py (1143B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from a2_controller_launch_handoff_models import A2ControllerLaunchHandoff   def _write_json(path: Path, payload: dict) -> None

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
