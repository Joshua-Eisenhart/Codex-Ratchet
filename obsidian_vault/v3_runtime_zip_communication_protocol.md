---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_zip_communication_protocol::b0313fcc89637481"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_zip_communication_protocol
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_zip_communication_protocol::b0313fcc89637481`

## Description
zip_communication_protocol.py (1471B): import hashlib import json from pathlib import Path   def _sha256_bytes(data: bytes) -> str:     return hashlib.sha256(data).hexdigest()   def _canonical_bytes(payload: dict) -> bytes:     return json.dumps(payload, sort_keys=True, separators=(",", "

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[test_run_a1_autoratchet_cycle_audit.py]] → **SOURCE_MAP_PASS**
