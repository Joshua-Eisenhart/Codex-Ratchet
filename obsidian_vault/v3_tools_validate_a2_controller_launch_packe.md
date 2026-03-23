---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_validate_a2_controller_launch_packe::d8c1e5d58fe7d053"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_validate_a2_controller_launch_packe
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_validate_a2_controller_launch_packe::d8c1e5d58fe7d053`

## Description
validate_a2_controller_launch_packet.py (3853B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import re import sys from pathlib import Path   SCHEMA = "A2_CONTROLLER_LAUNCH_PACKET_v1" THREAD_CLASS = "A2_CONTROLLER" MODE = "CONTROLLER_ONLY"   def _load_json(

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[a2_controller_launch_packet]]

## Inward Relations
- [[stage_browser_observed_thread_packet.py]] → **SOURCE_MAP_PASS**
