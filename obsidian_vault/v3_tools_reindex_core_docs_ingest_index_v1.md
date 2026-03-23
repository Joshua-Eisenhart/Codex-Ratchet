---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_reindex_core_docs_ingest_index_v1::2d22576ec482c368"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_reindex_core_docs_ingest_index_v1
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_reindex_core_docs_ingest_index_v1::2d22576ec482c368`

## Description
reindex_core_docs_ingest_index_v1.py (4288B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import time from pathlib import Path   def _sha256_file(path: Path) -> str:     h = hashlib.sha256()     with path.open("rb") as f:         for chun

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[index]]

## Inward Relations
- [[reindex_core_docs_ingest_index_v1.py]] → **SOURCE_MAP_PASS**
- [[reindex_core_docs_ingest_index_v1_py]] → **STRUCTURALLY_RELATED**
- [[a2_state_v3_core_docs_ingest_index_v1]] → **EXCLUDES**
- [[sysrepair_v2_core_docs_ingest_index_v1]] → **EXCLUDES**
- [[sysrepair_v3_core_docs_ingest_index_v1]] → **EXCLUDES**
- [[sysrepair_v4_core_docs_ingest_index_v1]] → **EXCLUDES**
- [[core_docs_ingest_index_v1_sha256]] → **EXCLUDES**
- [[core_docs_ingest_index_v1_json]] → **EXCLUDES**
