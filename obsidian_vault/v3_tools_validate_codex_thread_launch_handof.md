---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_validate_codex_thread_launch_handof::be1fd5157c06fe00"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_validate_codex_thread_launch_handof
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_validate_codex_thread_launch_handof::be1fd5157c06fe00`

## Description
validate_codex_thread_launch_handoff.py (11548B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import sys from pathlib import Path   ALLOWED_SCHEMAS = {     "A2_CONTROLLER_LAUNCH_HANDOFF_v1",     "A2_WORKER_LAUNCH_HANDOFF_v1",     "A1_WORKER_L

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[stage_browser_observed_thread_packet.py]] → **SOURCE_MAP_PASS**
