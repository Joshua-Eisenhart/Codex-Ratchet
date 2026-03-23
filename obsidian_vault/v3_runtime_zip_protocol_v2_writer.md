---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_zip_protocol_v2_writer::8e12ce046e91f7e0"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_zip_protocol_v2_writer
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_zip_protocol_v2_writer::8e12ce046e91f7e0`

## Description
zip_protocol_v2_writer.py (4018B): import hashlib import json import zipfile from dataclasses import dataclass from pathlib import Path   _FIXED_ZIP_DATETIME = (1980, 1, 1, 0, 0, 0)   def _sha256_bytes(data: bytes) -> str:     return hashlib.sha256(data).hexdigest()   def _canonical_j

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[ZIP_PROTOCOL_V2]]

## Inward Relations
- [[zip_protocol_v2_writer.py]] → **SOURCE_MAP_PASS**
