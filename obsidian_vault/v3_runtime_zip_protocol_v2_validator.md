---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_zip_protocol_v2_validator::fd77e32952d5abee"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_zip_protocol_v2_validator
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_zip_protocol_v2_validator::fd77e32952d5abee`

## Description
zip_protocol_v2_validator.py (20238B): from __future__ import annotations  import hashlib import json import re import zipfile from pathlib import PurePosixPath  from containers import parse_export_block, parse_sim_evidence_pack   _RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$") _RFC33

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[sim_evidence]]
- **DEPENDS_ON** → [[ZIP_PROTOCOL_V2]]
- **DEPENDS_ON** → [[export_block]]

## Inward Relations
- [[test_run_a1_autoratchet_cycle_audit.py]] → **SOURCE_MAP_PASS**
