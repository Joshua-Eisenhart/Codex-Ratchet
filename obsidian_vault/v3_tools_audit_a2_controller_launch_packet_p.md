---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_a2_controller_launch_packet_p::c42c1b824cd1d9aa"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_a2_controller_launch_packet_p
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_a2_controller_launch_packet_p::c42c1b824cd1d9aa`

## Description
audit_a2_controller_launch_packet_pydantic.py (964B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from a2_controller_launch_packet_models import load_a2_controller_launch_packet   def main(argv: list[str]) -> int:     parser

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[a2_controller_launch_packet]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
