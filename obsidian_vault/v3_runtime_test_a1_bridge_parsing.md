---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_bridge_parsing::4f5a318d133f8a49"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a1_bridge_parsing
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_bridge_parsing::4f5a318d133f8a49`

## Description
test_a1_bridge_parsing.py (6529B): import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from a1_bridge import _coerce_strategy, _parse_strategy_output_text   class TestA1BridgeParsing(unittest.TestCase):     def

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[output]]

## Inward Relations
- [[README.md]] → **SOURCE_MAP_PASS**
