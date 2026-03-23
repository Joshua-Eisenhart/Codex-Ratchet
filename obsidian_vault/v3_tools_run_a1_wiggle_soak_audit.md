---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_a1_wiggle_soak_audit::5fa1e3773e73bdfe"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_a1_wiggle_soak_audit
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_a1_wiggle_soak_audit::5fa1e3773e73bdfe`

## Description
run_a1_wiggle_soak_audit.py (8257B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path   def _read_json(path: Path) -> dict:     if not path.exists():         return {}     try:         data = json.loads(path.read_text(encodi

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[reindex_core_docs_ingest_index_v1.py]] → **SOURCE_MAP_PASS**
