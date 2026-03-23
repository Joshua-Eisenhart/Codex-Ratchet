---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_build_a2_controller_send_text_::1ca973008f3a5967"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_build_a2_controller_send_text_
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_build_a2_controller_send_text_::1ca973008f3a5967`

## Description
test_build_a2_controller_send_text_from_packet.py (1465B): from __future__ import annotations  import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[3] TOOLS = BASE / "tools" sys.path.insert(0, str(TOOLS))  from build_a2_controller_send_text_from_packet import build_sen

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[send_text]]

## Inward Relations
- [[test_audit_a1_current_queue_note_alignment.py]] → **SOURCE_MAP_PASS**
