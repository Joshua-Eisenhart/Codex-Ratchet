---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_a1_autoratchet_cycle_audit::ae79ab4bc1b7f7df"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_a1_autoratchet_cycle_audit
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_a1_autoratchet_cycle_audit::ae79ab4bc1b7f7df`

## Description
run_a1_autoratchet_cycle_audit.py (62025B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import zipfile from pathlib import Path   def _read_json(path: Path) -> dict:     if not path.exists():         return {}     try:         data = json.loads(path.r

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[reindex_core_docs_ingest_index_v1.py]] → **SOURCE_MAP_PASS**
- [[test_run_a1_autoratchet_cycle_audit_py]] → **EXCLUDES**
- [[run_a1_autoratchet_cycle_audit_py]] → **EXCLUDES**
- [[v3_runtime_test_run_a1_autoratchet_cycle_audit]] → **STRUCTURALLY_RELATED**
