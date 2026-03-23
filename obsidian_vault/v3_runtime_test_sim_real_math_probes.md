---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_sim_real_math_probes::e749d54331bc1b01"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_sim_real_math_probes
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_sim_real_math_probes::e749d54331bc1b01`

## Description
test_sim_real_math_probes.py (21497B): import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from sim_engine import SimEngine, SimTask from state import KernelState   class TestSimRealMathProbes(unittest.TestCase):  

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[test_run_a1_autoratchet_cycle_audit.py]] → **SOURCE_MAP_PASS**
- [[test_sim_real_math_probes_py]] → **STRUCTURALLY_RELATED**
