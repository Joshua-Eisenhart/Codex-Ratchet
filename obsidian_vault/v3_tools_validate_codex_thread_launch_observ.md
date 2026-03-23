---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_validate_codex_thread_launch_observ::df5ca7f6438e3858"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_validate_codex_thread_launch_observ
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_validate_codex_thread_launch_observ::df5ca7f6438e3858`

## Description
validate_codex_thread_launch_observed_packet.py (3021B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   SCHEMA = "CODEX_THREAD_LAUNCH_OBSERVED_PACKET_v1" ALLOWED_THREAD_CLASSES = {"A2_CONTROLLER", "A2_WORKER", "A1_WORKER"} ALLOWE

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[stage_browser_observed_thread_packet.py]] → **SOURCE_MAP_PASS**
