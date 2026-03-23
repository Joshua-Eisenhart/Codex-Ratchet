---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_rebuild_a2_doc_index_json::62a0ed9d47ede5c3"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_rebuild_a2_doc_index_json
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_rebuild_a2_doc_index_json::62a0ed9d47ede5c3`

## Description
rebuild_a2_doc_index_json.py (3718B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import time from pathlib import Path   def _sha256_file(path: Path) -> str:     h = hashlib.sha256()     with path.open("rb") as f:         for chun

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[index]]
- **DEPENDS_ON** → [[doc_index]]
- **DEPENDS_ON** → [[doc_index_json]]

## Inward Relations
- [[extract_parallel_codex_worker_result.py]] → **SOURCE_MAP_PASS**
