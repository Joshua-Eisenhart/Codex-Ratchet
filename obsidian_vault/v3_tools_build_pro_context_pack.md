---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_build_pro_context_pack::991ca67d22fea9a6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_build_pro_context_pack
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_build_pro_context_pack::991ca67d22fea9a6`

## Description
build_pro_context_pack.py (8013B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import os import re import shutil import sys from dataclasses import dataclass from pathlib import Path   def _infer_repo_root(start: Path) -> Path:

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[start]]

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
