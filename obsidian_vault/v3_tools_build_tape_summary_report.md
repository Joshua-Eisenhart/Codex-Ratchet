---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_build_tape_summary_report::d66df43b72b680a1"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_build_tape_summary_report
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_build_tape_summary_report::d66df43b72b680a1`

## Description
build_tape_summary_report.py (3753B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json from pathlib import Path   def _sha256_file(path: Path) -> str:     digest = hashlib.sha256()     with path.open("rb") as handle:         for chunk 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
- [[v3_spec_tape_summary_report_v1schema]] → **STRUCTURALLY_RELATED**
- [[build_tape_summary_report_py]] → **STRUCTURALLY_RELATED**
- [[tape_summary_report_v1_schema_json]] → **STRUCTURALLY_RELATED**
