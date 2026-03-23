---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_bootpack_sync_audit::c3c567b7e2a16754"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_bootpack_sync_audit
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_bootpack_sync_audit::c3c567b7e2a16754`

## Description
bootpack_sync_audit.py (6116B): #!/usr/bin/env python3 from __future__ import annotations  import hashlib import json import re from pathlib import Path from typing import Dict, List   def sha256_text(text: str) -> str:     return hashlib.sha256(text.encode("utf-8")).hexdigest()   

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
