---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_compile_first_controller_a1_launch_::7f21f6ea3c993d7f"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_compile_first_controller_a1_launch_
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_compile_first_controller_a1_launch_::7f21f6ea3c993d7f`

## Description
compile_first_controller_a1_launch_subset_graph.py (5689B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  import networkx as nx   def _require_abs_existing_path(raw: str, key: str) -> Path:     path = Path(raw)     if not path.is_ab

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
