---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_a2_worker_launch_from_packet::1e0ffb36578b4ac6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_a2_worker_launch_from_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_a2_worker_launch_from_packet::1e0ffb36578b4ac6`

## Description
run_a2_worker_launch_from_packet.py (2849B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from validate_a2_worker_launch_packet import validate as validate_packet   def _load_json(path: Path) -> dict:     if not path

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[reindex_core_docs_ingest_index_v1.py]] → **SOURCE_MAP_PASS**
