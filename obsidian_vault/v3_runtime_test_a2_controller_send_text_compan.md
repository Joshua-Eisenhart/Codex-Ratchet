---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a2_controller_send_text_compan::7e2ff82ae7a6a5ba"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a2_controller_send_text_compan
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a2_controller_send_text_compan::7e2ff82ae7a6a5ba`

## Description
test_a2_controller_send_text_companion_pydantic_stack.py (4377B): from __future__ import annotations  import json import subprocess import sys import tempfile import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[3] TOOLS = BASE / "tools" A2_STATE = BASE / "a2_state" SPEC_GRAPH_PYTHON = 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[send_text]]
- **DEPENDS_ON** → [[test_a2_controller_send_text_companion_pydantic_st]]

## Inward Relations
- [[test_a1_queue_status_packet.py]] → **SOURCE_MAP_PASS**
