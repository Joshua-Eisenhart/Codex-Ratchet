---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_storage_janitor::5f7f0bfd87f63908"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_storage_janitor
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_storage_janitor::5f7f0bfd87f63908`

## Description
storage_janitor.py (6695B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import datetime as dt import json import os import shutil from pathlib import Path   ROOT = Path(__file__).resolve().parents[2] RUNS_ROOT = ROOT / "system_v3" / "runs" LEGACY_

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[stage_browser_observed_thread_packet.py]] → **SOURCE_MAP_PASS**
- [[storage_janitor_py]] → **EXCLUDES**
