---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_sim_evidence_contract::f542de24c78f5cc6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_sim_evidence_contract
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_sim_evidence_contract::f542de24c78f5cc6`

## Description
test_sim_evidence_contract.py (3416B): import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from kernel import BootpackBKernel from state import KernelState   def _evidence_block(     sim_id: str = "S_SIM_ALPHA",   

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[sim_evidence]]
- **DEPENDS_ON** → [[sim_evidence_contract]]

## Inward Relations
- [[test_run_a1_autoratchet_cycle_audit.py]] → **SOURCE_MAP_PASS**
