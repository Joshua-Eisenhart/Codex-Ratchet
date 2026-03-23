---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_create_browser_codex_thread_target::db77a514a6296375"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_create_browser_codex_thread_target
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_create_browser_codex_thread_target::db77a514a6296375`

## Description
create_browser_codex_thread_target.py (2546B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER"} ALLOWED_TARGET_STATUS = {"READY", "STALE", "UNVERIFIED"} THREAD_PLATFORM 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[browser_codex_thread_target]]
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
