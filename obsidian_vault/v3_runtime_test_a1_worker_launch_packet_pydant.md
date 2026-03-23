---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_worker_launch_packet_pydant::c392edfa59676a18"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a1_worker_launch_packet_pydant
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_worker_launch_packet_pydant::c392edfa59676a18`

## Description
test_a1_worker_launch_packet_pydantic_stack.py (3262B): from __future__ import annotations  import json import subprocess import tempfile import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[3] TOOLS = BASE / "tools" SPEC_DRAFTS = BASE.parent / "work" / "audit_tmp" / "spec_obj

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[test_a1_worker_launch_packet_py]]

## Inward Relations
- [[test_a1_queue_status_packet.py]] → **SOURCE_MAP_PASS**
