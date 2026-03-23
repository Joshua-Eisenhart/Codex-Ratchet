---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_extract_auto_go_on_thread_result::e153638e8fe0dd76"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_extract_auto_go_on_thread_result
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_extract_auto_go_on_thread_result::e153638e8fe0dd76`

## Description
extract_auto_go_on_thread_result.py (7929B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import re import sys from datetime import datetime, timezone from pathlib import Path   ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER", "A2_CONTROLLER"} ALLOWE

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[emit_a2_controller_launch_packet_pydantic_schema.py]] → **SOURCE_MAP_PASS**
