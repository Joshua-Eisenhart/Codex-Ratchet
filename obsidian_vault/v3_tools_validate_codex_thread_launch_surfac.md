---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_validate_codex_thread_launch_surfac::16a3623afe9d7709"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_validate_codex_thread_launch_surfac
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_validate_codex_thread_launch_surfac::16a3623afe9d7709`

## Description
validate_codex_thread_launch_surface_capture_record.py (2687B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   SCHEMA = "CODEX_THREAD_LAUNCH_SURFACE_CAPTURE_RECORD_v1" ALLOWED_THREAD_CLASSES = {"A2_CONTROLLER", "A2_WORKER", "A1_WORKER"}

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[validate_codex_thread_launch_surface_capture_recor]]

## Inward Relations
- [[stage_browser_observed_thread_packet.py]] → **SOURCE_MAP_PASS**
