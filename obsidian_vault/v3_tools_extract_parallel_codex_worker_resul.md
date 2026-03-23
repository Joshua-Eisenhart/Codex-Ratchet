---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_extract_parallel_codex_worker_resul::16e1eda4cc0a7540"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_extract_parallel_codex_worker_resul
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_extract_parallel_codex_worker_resul::16e1eda4cc0a7540`

## Description
extract_parallel_codex_worker_result.py (4173B): #!/usr/bin/env python3 """Normalize one raw parallel Codex worker return into JSON for C0 evaluation."""  from __future__ import annotations  import argparse import json import re from pathlib import Path   ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[extract_parallel_codex_worker_result.py]] → **SOURCE_MAP_PASS**
