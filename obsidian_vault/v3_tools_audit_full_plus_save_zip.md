---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_full_plus_save_zip::c6735ba5ed7f48f5"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_full_plus_save_zip
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_full_plus_save_zip::c6735ba5ed7f48f5`

## Description
audit_full_plus_save_zip.py (5821B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import re import zipfile from pathlib import Path   _REQUIRED_MEMBERS = [     "THREAD_S_SAVE_SNAPSHOT_v2.txt",     "DUMP_LEDGER_BODIES.txt",     "DU

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **STRUCTURALLY_RELATED** → [[v3_tools_build_full_plus_save_zip]]
- **DEPENDS_ON** → [[thread_s_save_snapshot_v2]]
- **DEPENDS_ON** → [[dump_ledger_bodies]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
- [[full_plus_semantic_save_zip]] → **STRUCTURALLY_RELATED**
- [[v3_spec_73_full_plus_semantic_save_zip__v1]] → **STRUCTURALLY_RELATED**
- [[v3_spec_full_plus_save_gap_audit__2026_03_1]] → **STRUCTURALLY_RELATED**
- [[audit_full_plus_save_zip_py]] → **STRUCTURALLY_RELATED**
- [[full_plus_semantic_save]] → **STRUCTURALLY_RELATED**
