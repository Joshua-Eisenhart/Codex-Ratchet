---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_build_export_block_lint_report::780028d1588922c6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_build_export_block_lint_report
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_build_export_block_lint_report::780028d1588922c6`

## Description
build_export_block_lint_report.py (7156B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys import zipfile from collections import Counter from pathlib import Path   def _repo_root() -> Path:     return Path(__file__).resolve().parents[2]   BOO

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[export_block]]

## Inward Relations
- [[browser_go_on_helper.py]] → **SOURCE_MAP_PASS**
- [[v3_spec_export_block_lint_report_v1schema]] → **STRUCTURALLY_RELATED**
- [[build_export_block_lint_report_py]] → **STRUCTURALLY_RELATED**
- [[export_block_lint_report_v1_schema_json]] → **STRUCTURALLY_RELATED**
