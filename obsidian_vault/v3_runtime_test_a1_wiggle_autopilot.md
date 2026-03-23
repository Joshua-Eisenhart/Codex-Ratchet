---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_wiggle_autopilot::be6d1487fb087cb3"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a1_wiggle_autopilot
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_wiggle_autopilot::be6d1487fb087cb3`

## Description
test_a1_wiggle_autopilot.py (4704B): from __future__ import annotations  import sys import tempfile import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[3] sys.path.insert(0, str(BASE / "tools"))  from a1_wiggle_autopilot import (     _append_jsonl,     _app

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[test_a1_queue_status_packet.py]] → **SOURCE_MAP_PASS**
