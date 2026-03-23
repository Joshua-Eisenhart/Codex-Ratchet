---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_export_a2_to_a1_family_slice_graph::242796e8b99d8fa5"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_export_a2_to_a1_family_slice_graph
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_export_a2_to_a1_family_slice_graph::242796e8b99d8fa5`

## Description
export_a2_to_a1_family_slice_graph.py (1346B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  import networkx as nx  from a2_to_a1_family_slice_models import load_family_slice   def main(argv: list[str]) -> int:     pars

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]

## Inward Relations
- [[emit_a2_controller_launch_packet_pydantic_schema.py]] → **SOURCE_MAP_PASS**
