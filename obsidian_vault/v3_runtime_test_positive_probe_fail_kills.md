---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_positive_probe_fail_kills::aa7f5475824995ba"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_positive_probe_fail_kills
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_positive_probe_fail_kills::aa7f5475824995ba`

## Description
test_positive_probe_fail_kills.py (3088B): import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from pipeline import A0BSimPipeline from state import KernelState   def _wrap_export(content_lines: list[str], export_id: s

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[test_audit_a1_current_queue_note_alignment.py]] → **SOURCE_MAP_PASS**
- [[test_positive_probe_fail_kills_py]] → **STRUCTURALLY_RELATED**
