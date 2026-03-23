---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_a0_compile_gate::84e4a559d1190787"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_a0_compile_gate
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_a0_compile_gate::84e4a559d1190787`

## Description
run_a0_compile_gate.py (7474B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import re import zipfile from pathlib import Path   EXPORT_RE = re.compile(r"^export_block_(\d+)\.txt$") COMPILE_RE = re.compile(r"^compile_report_(

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[export_block]]

## Inward Relations
- [[reindex_core_docs_ingest_index_v1.py]] → **SOURCE_MAP_PASS**
