---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_a2_controller_send_text_compa::5d58e6165f51a6ca"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_a2_controller_send_text_compa
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_a2_controller_send_text_compa::5d58e6165f51a6ca`

## Description
audit_a2_controller_send_text_companion_pydantic.py (925B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from a2_controller_send_text_companion_models import load_a2_controller_send_text_companion   def main(argv: list[str]) -> int

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[send_text]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
