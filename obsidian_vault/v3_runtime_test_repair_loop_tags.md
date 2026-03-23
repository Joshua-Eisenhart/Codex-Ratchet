---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_repair_loop_tags::91bed14542f02d79"
type: "REFINED_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_repair_loop_tags
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_repair_loop_tags::91bed14542f02d79`

## Description
test_repair_loop_tags.py (3012B): import json import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from a0_compiler import compile_export_block from state import KernelState   def _load_strategy() -> dict:     

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 2 sources, 2 batches, 3 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[export_block]]

## Inward Relations
- [[test_audit_a1_current_queue_note_alignment.py]] → **SOURCE_MAP_PASS**
- [[zip_protocol_v2_writer.py]] → **OVERLAPS**
- [[test_repair_loop_tags_py]] → **EXCLUDES**
