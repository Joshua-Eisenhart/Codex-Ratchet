---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_export_a1_worker_launch_packet_grap::cc8429cc37e43dd8"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_export_a1_worker_launch_packet_grap
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_export_a1_worker_launch_packet_grap::cc8429cc37e43dd8`

## Description
export_a1_worker_launch_packet_graph.py (903B): #!/usr/bin/env python3 from __future__ import annotations  import argparse from pathlib import Path  import networkx as nx  from a1_worker_launch_packet_models import load_a1_worker_launch_packet   def main() -> int:     parser = argparse.ArgumentPar

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[emit_a2_controller_launch_packet_pydantic_schema.py]] → **SOURCE_MAP_PASS**
