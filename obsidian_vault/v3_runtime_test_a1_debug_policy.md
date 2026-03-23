---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_debug_policy::f52c19d7f120397e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a1_debug_policy
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_debug_policy::f52c19d7f120397e`

## Description
test_a1_debug_policy.py (1640B): import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from a1_debug_policy import evaluate_escalation   class TestA1DebugPolicy(unittest.TestCase):     def test_no_escalation_wh

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[debug]]

## Inward Relations
- [[README.md]] → **SOURCE_MAP_PASS**
- [[a1_debug_policy_py]] → **EXCLUDES**
- [[test_a1_debug_policy_py]] → **EXCLUDES**
