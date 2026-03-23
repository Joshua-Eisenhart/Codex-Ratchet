---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_a2_controller_launch_handoff_::311fe471424e00fb"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_a2_controller_launch_handoff_
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_a2_controller_launch_handoff_::311fe471424e00fb`

## Description
audit_a2_controller_launch_handoff_pydantic.py (898B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from a2_controller_launch_handoff_models import load_a2_controller_launch_handoff   def main(argv: list[str]) -> int:     pars

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
