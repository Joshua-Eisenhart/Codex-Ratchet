---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_worker_launch_packet::27f0ec56fe259ce4"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a1_worker_launch_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_worker_launch_packet::27f0ec56fe259ce4`

## Description
test_a1_worker_launch_packet.py (6576B): from __future__ import annotations  import json import subprocess import sys import tempfile import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[3] TOOLS = BASE / "tools" sys.path.insert(0, str(TOOLS))  from build_a1_wor

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[test_a1_queue_status_packet.py]] → **SOURCE_MAP_PASS**
