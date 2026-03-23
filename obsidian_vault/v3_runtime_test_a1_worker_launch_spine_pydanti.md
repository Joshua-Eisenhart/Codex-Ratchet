---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_worker_launch_spine_pydanti::f84092eb00cf1ac6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a1_worker_launch_spine_pydanti
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_worker_launch_spine_pydanti::f84092eb00cf1ac6`

## Description
test_a1_worker_launch_spine_pydantic_stack.py (2733B): from __future__ import annotations  import json import subprocess import tempfile import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[3] TOOLS = BASE / "tools" SPEC_DRAFTS = BASE.parent / "work" / "audit_tmp" / "spec_obj

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[test_a1_queue_status_packet.py]] → **SOURCE_MAP_PASS**
