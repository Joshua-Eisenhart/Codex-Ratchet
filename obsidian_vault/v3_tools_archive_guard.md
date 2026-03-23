---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_archive_guard::c201cbf03f7ad250"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_archive_guard
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_archive_guard::c201cbf03f7ad250`

## Description
archive_guard.py (3204B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import os from pathlib import Path   def _infer_repo_root(start: Path) -> Path:     cur = start.resolve()     if cur.is_file():         cur = cur.parent     for _ 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[start]]

## Inward Relations
- [[a1_wiggle_autopilot.py]] → **SOURCE_MAP_PASS**
- [[archive_guard_py]] → **EXCLUDES**
