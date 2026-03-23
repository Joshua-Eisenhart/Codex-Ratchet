---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_create_codex_thread_launch_observed::f5e1cf04fa53c789"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_create_codex_thread_launch_observed
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_create_codex_thread_launch_observed::f5e1cf04fa53c789`

## Description
create_codex_thread_launch_observed_packet.py (3110B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   ALLOWED_THREAD_CLASSES = {"A2_CONTROLLER", "A2_WORKER", "A1_WORKER"} ALLOWED_COMPOSER_READY = {"YES", "NO"} ALLOWED_CAPTURE_M

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
- [[create_codex_thread_launch_observed_packet_py]] → **EXCLUDES**
