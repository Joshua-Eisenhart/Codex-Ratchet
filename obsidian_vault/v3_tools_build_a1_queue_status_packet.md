---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_build_a1_queue_status_packet::e51fd23efd4553a1"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_build_a1_queue_status_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_build_a1_queue_status_packet::e51fd23efd4553a1`

## Description
build_a1_queue_status_packet.py (10386B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import subprocess import sys from pathlib import Path  from validate_a1_queue_status_packet import validate as validate_queue_packet   SCHEMA = "A1_QUEUE_STATUS_PA

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[browser_go_on_helper.py]] → **SOURCE_MAP_PASS**
