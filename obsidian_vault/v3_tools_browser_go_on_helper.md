---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_browser_go_on_helper::bb4492358cfbf854"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_browser_go_on_helper
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_browser_go_on_helper::bb4492358cfbf854`

## Description
browser_go_on_helper.py (8979B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from datetime import datetime, timezone from pathlib import Path   ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER"} ALLOWED_MESSAGE = "go on" ALLOWED

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[browser_go_on_helper.py]] → **SOURCE_MAP_PASS**
