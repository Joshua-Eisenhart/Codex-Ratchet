---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_containers::ae125a2147c58f9a"
type: "REFINED_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_containers
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_containers::ae125a2147c58f9a`

## Description
containers.py (8536B): import re from dataclasses import dataclass   _BEGIN_EXPORT_RE = re.compile(r"^BEGIN EXPORT_BLOCK (v\d+)$") _END_EXPORT_RE = re.compile(r"^END EXPORT_BLOCK (v\d+)$") _BEGIN_SIM_RE = re.compile(r"^BEGIN SIM_EVIDENCE v1$") _END_SIM_RE = re.compile(r"^E

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 3 sources, 3 batches, 3 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[sim_evidence]]
- **DEPENDS_ON** → [[sim_evidence_v1]]
- **DEPENDS_ON** → [[export_block]]

## Inward Relations
- [[NONCANONICAL_RUNTIME_FROZEN_IMPORT_BLOCKED_FILES.txt]] → **SOURCE_MAP_PASS**
- [[zip_protocol_v2_writer.py]] → **OVERLAPS**
- [[a0_generator_v2.py]] → **OVERLAPS**
