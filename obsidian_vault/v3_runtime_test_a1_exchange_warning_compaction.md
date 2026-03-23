---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_exchange_warning_compaction::3cee7396d27f413e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a1_exchange_warning_compaction
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_exchange_warning_compaction::3cee7396d27f413e`

## Description
test_a1_exchange_warning_compaction.py (12646B): from __future__ import annotations  import json import sys import tempfile import unittest from pathlib import Path from unittest import mock  BASE = Path(__file__).resolve().parents[3] sys.path.insert(0, str(BASE / "tools"))  from a1_external_memo_b

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[external]]
- **DEPENDS_ON** → [[compaction]]

## Inward Relations
- [[README.md]] → **SOURCE_MAP_PASS**
- [[test_a1_exchange_warning_compaction_py]] → **STRUCTURALLY_RELATED**
