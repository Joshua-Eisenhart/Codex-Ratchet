---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_authority_coverage_audit::a64b200931dd83e4"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_authority_coverage_audit
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_authority_coverage_audit::a64b200931dd83e4`

## Description
authority_coverage_audit.py (8237B): #!/usr/bin/env python3 from __future__ import annotations  import hashlib import json import os import re from dataclasses import dataclass from pathlib import Path from typing import Dict, List, Set, Tuple   def _infer_repo_root(start: Path) -> Path

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[start]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
- [[authority_coverage_audit_py]] → **EXCLUDES**
