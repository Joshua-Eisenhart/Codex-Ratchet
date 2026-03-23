---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_export_a2_controller_send_text_comp::7bf98fa4c7f51a87"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_export_a2_controller_send_text_comp
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_export_a2_controller_send_text_comp::7bf98fa4c7f51a87`

## Description
export_a2_controller_send_text_companion_graph.py (1307B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  import networkx as nx  from a2_controller_send_text_companion_models import load_a2_controller_send_text_companion   def main(

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[send_text]]

## Inward Relations
- [[emit_a2_controller_launch_packet_pydantic_schema.py]] → **SOURCE_MAP_PASS**
