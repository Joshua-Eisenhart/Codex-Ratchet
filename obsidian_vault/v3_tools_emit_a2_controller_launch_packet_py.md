---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_emit_a2_controller_launch_packet_py::918f71efd8a8097a"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_emit_a2_controller_launch_packet_py
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_emit_a2_controller_launch_packet_py::918f71efd8a8097a`

## Description
emit_a2_controller_launch_packet_pydantic_schema.py (1131B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from a2_controller_launch_packet_models import A2ControllerLaunchPacket   def _write_json(path: Path, payload: dict) -> None: 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[a2_controller_launch_packet]]

## Inward Relations
- [[emit_a2_controller_launch_packet_pydantic_schema.py]] → **SOURCE_MAP_PASS**
