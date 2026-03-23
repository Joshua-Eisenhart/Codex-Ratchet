---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_init_run_surface::831ff5b21ec0457d"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_init_run_surface
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_init_run_surface::831ff5b21ec0457d`

## Description
init_run_surface.py (8313B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import re from datetime import datetime, timezone from pathlib import Path   HEX64_RE = re.compile(r"^[0-9a-f]{64}$") RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$") 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[extract_parallel_codex_worker_result.py]] → **SOURCE_MAP_PASS**
