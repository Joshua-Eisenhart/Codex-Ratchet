---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_export_a1_queue_surfaces_graph::7a94073f57b732be"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_export_a1_queue_surfaces_graph
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_export_a1_queue_surfaces_graph::7a94073f57b732be`

## Description
export_a1_queue_surfaces_graph.py (1603B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  import networkx as nx  from a1_queue_surface_models import load_queue_candidate_registry, load_queue_status_packet   def main(

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[emit_a2_controller_launch_packet_pydantic_schema.py]] → **SOURCE_MAP_PASS**
