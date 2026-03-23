---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_export_a1_worker_launch_handoff_gra::b4fb2e7bc598fe19"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_export_a1_worker_launch_handoff_gra
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_export_a1_worker_launch_handoff_gra::b4fb2e7bc598fe19`

## Description
export_a1_worker_launch_handoff_graph.py (911B): #!/usr/bin/env python3 from __future__ import annotations  import argparse from pathlib import Path  import networkx as nx  from a1_worker_launch_handoff_models import load_a1_worker_launch_handoff   def main() -> int:     parser = argparse.ArgumentP

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[emit_a2_controller_launch_packet_pydantic_schema.py]] → **SOURCE_MAP_PASS**
