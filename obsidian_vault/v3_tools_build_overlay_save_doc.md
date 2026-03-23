---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_build_overlay_save_doc::2ad3c2bfbc3d5c19"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_build_overlay_save_doc
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_build_overlay_save_doc::2ad3c2bfbc3d5c19`

## Description
build_overlay_save_doc.py (2485B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import time from pathlib import Path   def _sha256_file(path: Path) -> str:     digest = hashlib.sha256()     with path.open("rb") as handle:       

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
