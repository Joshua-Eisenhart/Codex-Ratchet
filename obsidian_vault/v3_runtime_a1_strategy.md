---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_a1_strategy::96b69bbae6ef9806"
type: "REFINED_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_a1_strategy
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_a1_strategy::96b69bbae6ef9806`

## Description
a1_strategy.py (22523B): import hashlib import json from pathlib import Path   SCHEMA_V1 = "A1_STRATEGY_v1" SCHEMA_V2 = "A1_STRATEGY_v2" SUPPORTED_SCHEMAS = {SCHEMA_V1, SCHEMA_V2} FORBIDDEN_FIELDS = {"confidence", "probability", "embedding", "hidden_prompt", "raw_text"} ALLO

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 2 sources, 2 batches, 2 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[a1_strategy_v1]]

## Inward Relations
- [[NONCANONICAL_RUNTIME_FROZEN_IMPORT_BLOCKED_FILES.txt]] → **SOURCE_MAP_PASS**
- [[zip_protocol_v2_writer.py]] → **OVERLAPS**
