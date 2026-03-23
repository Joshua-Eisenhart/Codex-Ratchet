---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_build_a1_worker_send_text_from_pack::ab25218b50a5294b"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_build_a1_worker_send_text_from_pack
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_build_a1_worker_send_text_from_pack::ab25218b50a5294b`

## Description
build_a1_worker_send_text_from_packet.py (3303B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from run_a1_worker_launch_from_packet import build_result as build_gate_result from validate_a1_worker_launch_packet import va

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[send_text]]

## Inward Relations
- [[browser_go_on_helper.py]] → **SOURCE_MAP_PASS**
