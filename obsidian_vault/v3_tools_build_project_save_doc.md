---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_build_project_save_doc::42f39ff5f55d715c"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_build_project_save_doc
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_build_project_save_doc::42f39ff5f55d715c`

## Description
build_project_save_doc.py (6898B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import time import zipfile from pathlib import Path   FULL_PLUS_REQUIRED_MEMBERS = (     "restore/THREAD_S_SAVE_SNAPSHOT_v2.txt",     "restore/DUMP_

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[thread_s_save_snapshot_v2]]

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
