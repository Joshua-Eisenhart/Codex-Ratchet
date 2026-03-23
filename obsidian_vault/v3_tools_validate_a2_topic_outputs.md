---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_validate_a2_topic_outputs::aba3ef153065a8f8"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_validate_a2_topic_outputs
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_validate_a2_topic_outputs::aba3ef153065a8f8`

## Description
validate_a2_topic_outputs.py (7622B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import os import re import sys import zipfile from dataclasses import dataclass from pathlib import Path   def _infer_repo_root(start: Path) -> Path:     cur = sta

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[start]]
- **EXCLUDES** → [[validate_a2_topic_outputs_py]]

## Inward Relations
- [[stage_browser_observed_thread_packet.py]] → **SOURCE_MAP_PASS**
