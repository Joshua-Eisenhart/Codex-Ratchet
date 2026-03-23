---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_codex_browser_launch_from_obser::d3fc76eba0099c42"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_codex_browser_launch_from_obser
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_codex_browser_launch_from_obser::d3fc76eba0099c42`

## Description
run_codex_browser_launch_from_observed_packet.py (7080B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import subprocess import sys from pathlib import Path   REQUIRED_PACKET_FIELDS = [     "thread_class",     "launch_surface_title_observed",     "launch_route_obser

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[run_codex_browser_launch_from_capture_record.py]] → **SOURCE_MAP_PASS**
