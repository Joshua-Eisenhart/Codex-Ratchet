---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_a2_controller_launch_from_packe::1975a02c1b30256c"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_a2_controller_launch_from_packe
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_a2_controller_launch_from_packe::1975a02c1b30256c`

## Description
run_a2_controller_launch_from_packet.py (3254B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from validate_a2_controller_launch_packet import validate as validate_packet   ALLOWED_FIRST_ACTIONS = [     "weighted state r

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[a2_controller_launch_packet]]

## Inward Relations
- [[reindex_core_docs_ingest_index_v1.py]] → **SOURCE_MAP_PASS**
