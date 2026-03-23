---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_thread_closeout_extractor::07e3801ec538abf6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_thread_closeout_extractor
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_thread_closeout_extractor::07e3801ec538abf6`

## Description
test_thread_closeout_extractor.py (7100B): from __future__ import annotations  import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[3] TOOLS = BASE / "tools" WORK = BASE.parent / "work" / "audit_tmp" / "thread_closeout_packets" sys.path.insert(0, str(TO

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[test_run_a1_autoratchet_cycle_audit.py]] → **SOURCE_MAP_PASS**
- [[a2_worker__thread_closeout_extractor_patch__2026_0]] → **EXCLUDES**
- [[test_thread_closeout_extractor_py]] → **EXCLUDES**
