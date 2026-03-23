---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_append_thread_closeout_packet::c2f64d6e8eff0918"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_append_thread_closeout_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_append_thread_closeout_packet::c2f64d6e8eff0918`

## Description
append_thread_closeout_packet.py (5783B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   ALLOWED_DECISIONS = {     "STOP",     "CONTINUE_ONE_BOUNDED_STEP",     "CORRECT_LANE_LATER", }  ALLOWED_DIAGNOSES = {     "he

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[a1_wiggle_autopilot.py]] → **SOURCE_MAP_PASS**
- [[append_thread_closeout_packet_py]] → **STRUCTURALLY_RELATED**
