---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_emit_a2_controller_send_text_compan::481ce8cfa253f925"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_emit_a2_controller_send_text_compan
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_emit_a2_controller_send_text_compan::481ce8cfa253f925`

## Description
emit_a2_controller_send_text_companion_pydantic_schema.py (1166B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from a2_controller_send_text_companion_models import A2ControllerSendTextCompanion   def _write_json(path: Path, payload: dict

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[send_text]]
- **DEPENDS_ON** → [[emit_a2_controller_send_text_companion_pydantic_sc]]

## Inward Relations
- [[emit_a2_controller_launch_packet_pydantic_schema.py]] → **SOURCE_MAP_PASS**
