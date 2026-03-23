---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_create_a2_controller_launch_packet::3a783ed6d0d49de6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_create_a2_controller_launch_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_create_a2_controller_launch_packet::3a783ed6d0d49de6`

## Description
create_a2_controller_launch_packet.py (3277B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   SCHEMA = "A2_CONTROLLER_LAUNCH_PACKET_v1" THREAD_CLASS = "A2_CONTROLLER" MODE = "CONTROLLER_ONLY"   def _require_text(value: 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[value]]
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[a2_controller_launch_packet]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
