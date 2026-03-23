---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_create_browser_target_from_capture_::8300b325e14a8212"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_create_browser_target_from_capture_
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_create_browser_target_from_capture_::8300b325e14a8212`

## Description
create_browser_target_from_capture_record.py (4422B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER"} ALLOWED_CAPTURE_METHODS = {"MANUAL_OPERATOR", "PLAYWRIGHT_CAPTURE"} ALLOW

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
- [[create_browser_codex_thread_capture_record_py]] → **EXCLUDES**
- [[create_browser_target_from_capture_record_py]] → **EXCLUDES**
- [[create_codex_thread_launch_target_from_capture_rec]] → **EXCLUDES**
- [[create_codex_thread_launch_surface_capture_record_]] → **EXCLUDES**
