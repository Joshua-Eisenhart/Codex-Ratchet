---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_ingest_downloads::f0fc0a9bf07c1415"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_ingest_downloads
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_ingest_downloads::f0fc0a9bf07c1415`

## Description
ingest_downloads.py (7887B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import shutil import subprocess import sys import tempfile import zipfile from dataclasses import dataclass from pathlib import Path   @dataclass(fr

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
- [[ingest_downloads_py]] → **EXCLUDES**
