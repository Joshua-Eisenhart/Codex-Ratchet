---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_extract_thread_s_snapshot_from_sema::69feed04a7a09e13"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_extract_thread_s_snapshot_from_sema
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_extract_thread_s_snapshot_from_sema::69feed04a7a09e13`

## Description
extract_thread_s_snapshot_from_semantic_save.py (5710B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import time import zipfile from pathlib import Path   REQUIRED_FULL_PLUS_MEMBERS = (     "THREAD_S_SAVE_SNAPSHOT_v2.txt",     "DUMP_LEDGER_BODIES.tx

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[thread_s_save_snapshot_v2]]
- **DEPENDS_ON** → [[dump_ledger_bodies]]

## Inward Relations
- [[extract_parallel_codex_worker_result.py]] → **SOURCE_MAP_PASS**
