---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_a1_queue_surfaces_pydantic::059df22e514aafd5"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_a1_queue_surfaces_pydantic
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_a1_queue_surfaces_pydantic::059df22e514aafd5`

## Description
audit_a1_queue_surfaces_pydantic.py (2040B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from a1_queue_surface_models import load_queue_candidate_registry, load_queue_status_packet   def main(argv: list[str]) -> int

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
