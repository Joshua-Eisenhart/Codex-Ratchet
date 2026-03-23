---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_sprawl_guard::4bc21e59c3ea8afa"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_sprawl_guard
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_sprawl_guard::4bc21e59c3ea8afa`

## Description
sprawl_guard.py (3679B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import os from pathlib import Path   def _infer_repo_root(start: Path) -> Path:     cur = start.resolve()     if cur.is_file():         cur = cur.parent     for _ 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[start]]

## Inward Relations
- [[run_codex_browser_launch_from_capture_record.py]] → **SOURCE_MAP_PASS**
- [[sprawl_guard_py]] → **EXCLUDES**
