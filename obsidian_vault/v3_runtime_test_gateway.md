---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_gateway::dec4924701e744c2"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_gateway
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_gateway::dec4924701e744c2`

## Description
test_gateway.py (5944B): import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from gateway import BootpackBGateway from kernel import BootpackBKernel from state import KernelState   def _wrap_export(co

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[test_audit_a1_current_queue_note_alignment.py]] → **SOURCE_MAP_PASS**
