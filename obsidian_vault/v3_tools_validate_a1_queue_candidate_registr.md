---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_validate_a1_queue_candidate_registr::5d7ef058d9447d46"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_validate_a1_queue_candidate_registr
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_validate_a1_queue_candidate_registr::5d7ef058d9447d46`

## Description
validate_a1_queue_candidate_registry.py (2750B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   SCHEMA = "A1_QUEUE_CANDIDATE_REGISTRY_v1"   def _load_json(path: Path) -> dict:     if not path.exists():         raise Syste

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **EXCLUDES** → [[validate_a1_queue_candidate_registry_py]]

## Inward Relations
- [[stage_browser_observed_thread_packet.py]] → **SOURCE_MAP_PASS**
