---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_build_instrumentation_report::e428d68017a58068"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_build_instrumentation_report
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_build_instrumentation_report::e428d68017a58068`

## Description
build_instrumentation_report.py (4735B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from collections import Counter from pathlib import Path   def _read_json(path: Path) -> dict:     if not path.exists():         return {}     try:         return 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
