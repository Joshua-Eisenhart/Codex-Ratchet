---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_build_rosetta_map::645fa491e78a5ae1"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_build_rosetta_map
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_build_rosetta_map::645fa491e78a5ae1`

## Description
build_rosetta_map.py (9224B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import re import time from pathlib import Path   VERSION_SUFFIX_RE = re.compile(r"_v\d+(?:\.\d+)?$", re.IGNORECASE) VERSIONED_ID_RE = re.compile(r"\b([A-Z][A-Z0-9]

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
