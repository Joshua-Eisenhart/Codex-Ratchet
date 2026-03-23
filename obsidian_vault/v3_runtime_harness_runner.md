---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_harness_runner::020216cc9037f5b7"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_harness_runner
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_harness_runner::020216cc9037f5b7`

## Description
harness_runner.py (4455B): from __future__ import annotations  import argparse import json import sys from pathlib import Path from typing import Any  THIS_DIR = Path(__file__).resolve().parent TOOLS_DIR = THIS_DIR.parents[1] / "tools" if str(TOOLS_DIR) not in sys.path:     sy

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[README.md]] → **SOURCE_MAP_PASS**
- [[harness_runner_py]] → **EXCLUDES**
