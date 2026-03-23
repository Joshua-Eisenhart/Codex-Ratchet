---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_build_term_chain_report::2c1f7e045d794ce7"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_build_term_chain_report
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_build_term_chain_report::2c1f7e045d794ce7`

## Description
build_term_chain_report.py (4144B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import re import sys from pathlib import Path   def _repo_root() -> Path:     return Path(__file__).resolve().parents[2]   BOOTPACK_ROOT = _repo_root() / "system_v

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
- [[v3_spec_term_chain_report_v1schema]] → **EXCLUDES**
- [[build_term_chain_report_py]] → **EXCLUDES**
- [[term_chain_report_v1_schema_json]] → **EXCLUDES**
