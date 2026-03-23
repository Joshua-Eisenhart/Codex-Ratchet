---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_build_a1_worker_launch_packet_::4d8324a2f6613e48"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_build_a1_worker_launch_packet_
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_build_a1_worker_launch_packet_::4d8324a2f6613e48`

## Description
test_build_a1_worker_launch_packet_from_family_slice.py (16373B): from __future__ import annotations  import json import subprocess import sys import tempfile import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[3] TOOLS = BASE / "tools" SPEC_DRAFTS = BASE.parent / "work" / "audit_tmp" 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[test_build_a1_worker_launch_packet_from_family_sli]]

## Inward Relations
- [[test_audit_a1_current_queue_note_alignment.py]] → **SOURCE_MAP_PASS**
