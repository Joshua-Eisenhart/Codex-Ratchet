---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_export_a2_controller_launch_packet_::5ef4bbb217734eae"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_export_a2_controller_launch_packet_
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_export_a2_controller_launch_packet_::5ef4bbb217734eae`

## Description
export_a2_controller_launch_packet_graph.py (1265B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  import networkx as nx  from a2_controller_launch_packet_models import load_a2_controller_launch_packet   def main(argv: list[s

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[a2_controller_launch_packet]]

## Inward Relations
- [[emit_a2_controller_launch_packet_pydantic_schema.py]] → **SOURCE_MAP_PASS**
