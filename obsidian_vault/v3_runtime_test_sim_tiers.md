---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_sim_tiers::410e93f1c1b166ba"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_sim_tiers
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_sim_tiers::410e93f1c1b166ba`

## Description
test_sim_tiers.py (15412B): import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from kernel import BootpackBKernel from pipeline import A0BSimPipeline from sim_dispatcher import A0SimDispatcher from sim_

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[dispatcher]]

## Inward Relations
- [[test_run_a1_autoratchet_cycle_audit.py]] → **SOURCE_MAP_PASS**
