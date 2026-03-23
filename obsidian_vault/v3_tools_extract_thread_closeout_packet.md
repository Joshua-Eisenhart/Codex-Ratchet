---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_extract_thread_closeout_packet::c676e8457fb350e0"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_extract_thread_closeout_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_extract_thread_closeout_packet::c676e8457fb350e0`

## Description
extract_thread_closeout_packet.py (23894B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import re import sys from datetime import datetime, timezone from pathlib import Path   DIAGNOSES = {     "healthy_but_ready_to_stop",     "healthy_but_needs_one_b

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[extract_parallel_codex_worker_result.py]] → **SOURCE_MAP_PASS**
