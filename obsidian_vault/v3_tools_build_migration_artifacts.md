---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_build_migration_artifacts::d34cb7084275c1de"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_build_migration_artifacts
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_build_migration_artifacts::d34cb7084275c1de`

## Description
build_migration_artifacts.py (7450B): #!/usr/bin/env python3 from __future__ import annotations  import json import os from pathlib import Path from typing import Dict, List   def write_json(path: Path, obj) -> None:     path.parent.mkdir(parents=True, exist_ok=True)     path.write_text(

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[migration]]

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
- [[build_migration_artifacts_py]] → **EXCLUDES**
