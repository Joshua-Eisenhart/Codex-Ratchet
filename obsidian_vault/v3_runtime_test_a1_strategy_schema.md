---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_strategy_schema::6a417377ab680489"
type: "REFINED_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a1_strategy_schema
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_strategy_schema::6a417377ab680489`

## Description
test_a1_strategy_schema.py (7032B): import json import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from a1_strategy import validate_strategy   class TestA1StrategySchema(unittest.TestCase):     def test_sample_

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 2 sources, 2 batches, 2 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[strategy_schema]]

## Inward Relations
- [[test_a1_queue_status_packet.py]] → **SOURCE_MAP_PASS**
- [[zip_protocol_v2_writer.py]] → **OVERLAPS**
