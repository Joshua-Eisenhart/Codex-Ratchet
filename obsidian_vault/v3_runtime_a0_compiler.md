---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_a0_compiler::789740e13b84a99d"
type: "REFINED_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_a0_compiler
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_a0_compiler::789740e13b84a99d`

## Description
a0_compiler.py (28846B): import copy import hashlib import json import re  from a1_strategy import SCHEMA_V1, SCHEMA_V2, canonical_strategy_bytes, validate_strategy from containers import build_export_block from state import KernelState   COMPILER_VERSION = "A0_COMPILER_v2" 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 2 sources, 2 batches, 2 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[export_block]]

## Inward Relations
- [[NONCANONICAL_RUNTIME_FROZEN_IMPORT_BLOCKED_FILES.txt]] → **SOURCE_MAP_PASS**
- [[zip_protocol_v2_writer.py]] → **OVERLAPS**
