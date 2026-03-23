---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_stage_browser_observed_thread_packe::fa4f23ed57f0e1e0"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_stage_browser_observed_thread_packe
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_stage_browser_observed_thread_packe::fa4f23ed57f0e1e0`

## Description
stage_browser_observed_thread_packet.py (3455B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from datetime import datetime, timezone from pathlib import Path   ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER"} ALLOWED_COMPOSER_READY = {"YES", 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[stage_browser_observed_thread_packet.py]] → **SOURCE_MAP_PASS**
