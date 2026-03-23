---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_browser_go_on_playwright_from_o::394de802a794e272"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_browser_go_on_playwright_from_o
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_browser_go_on_playwright_from_o::394de802a794e272`

## Description
run_browser_go_on_playwright_from_observed_packet.py (5270B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import subprocess import sys from pathlib import Path   REQUIRED_PACKET_FIELDS = [     "target_thread_id",     "thread_class",     "thread_title_observed",     "th

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[reindex_core_docs_ingest_index_v1.py]] → **SOURCE_MAP_PASS**
