---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a2_controller_launch_packet_py::ce3b415982c5fdeb"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a2_controller_launch_packet_py
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a2_controller_launch_packet_py::ce3b415982c5fdeb`

## Description
test_a2_controller_launch_packet_pydantic_stack.py (3088B): from __future__ import annotations  import json import subprocess import tempfile import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[3] TOOLS = BASE / "tools" A2_STATE = BASE / "a2_state" SPEC_DRAFTS = BASE.parent / "wo

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[a2_controller_launch_packet]]

## Inward Relations
- [[test_a1_queue_status_packet.py]] → **SOURCE_MAP_PASS**
