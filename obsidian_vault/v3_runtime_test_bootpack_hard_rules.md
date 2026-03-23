---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_bootpack_hard_rules::e5dcc61f7221b586"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_bootpack_hard_rules
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_bootpack_hard_rules::e5dcc61f7221b586`

## Description
test_bootpack_hard_rules.py (8448B): import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from kernel import BootpackBKernel from state import KernelState   def _wrap_export(content_lines: list[str], export_id: st

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[test_audit_a1_current_queue_note_alignment.py]] → **SOURCE_MAP_PASS**
- [[a2_seven_hard_rules]] → **EXCLUDES**
- [[a2_thread_boot_nine_hard_rules]] → **EXCLUDES**
- [[a1_thread_boot_eight_hard_rules]] → **EXCLUDES**
- [[sender_packet_hard_rules]] → **EXCLUDES**
- [[test_bootpack_hard_rules_py]] → **EXCLUDES**
- [[a2_hard_rules]] → **EXCLUDES**
- [[a2_thread_boot_nine_hard_rules]] → **STRUCTURALLY_RELATED**
- [[a1_thread_boot_eight_hard_rules]] → **STRUCTURALLY_RELATED**
- [[a2_seven_hard_rules]] → **STRUCTURALLY_RELATED**
- [[A2_THREAD_BOOT_NINE_HARD_RULES]] → **STRUCTURALLY_RELATED**
- [[A1_THREAD_BOOT_EIGHT_HARD_RULES]] → **STRUCTURALLY_RELATED**
- [[A2_SEVEN_HARD_RULES]] → **STRUCTURALLY_RELATED**
