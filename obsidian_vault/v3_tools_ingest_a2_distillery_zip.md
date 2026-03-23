---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_ingest_a2_distillery_zip::494a1d3e60b32849"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_ingest_a2_distillery_zip
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_ingest_a2_distillery_zip::494a1d3e60b32849`

## Description
ingest_a2_distillery_zip.py (6522B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import time import zipfile from pathlib import Path   MINING_SCHEMA_TO_LOG = {     "FUEL_DIGEST_v1": "fuel_digests.jsonl",     "ROSETTA_MAP_v1": "ro

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[extract_parallel_codex_worker_result.py]] → **SOURCE_MAP_PASS**
- [[ingest_a2_distillery_zip_py]] → **EXCLUDES**
