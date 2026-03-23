---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_a2_controller_launch_gate_res::e7e4c4aad1606275"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_a2_controller_launch_gate_res
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_a2_controller_launch_gate_res::e7e4c4aad1606275`

## Description
audit_a2_controller_launch_gate_result_pydantic.py (902B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from a2_controller_launch_gate_result_models import load_a2_controller_launch_gate_result   def main(argv: list[str]) -> int: 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
