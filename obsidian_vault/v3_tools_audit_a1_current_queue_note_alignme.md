---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_a1_current_queue_note_alignme::80f3c32f4792a8ae"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_a1_current_queue_note_alignme
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_a1_current_queue_note_alignme::80f3c32f4792a8ae`

## Description
audit_a1_current_queue_note_alignment.py (2470B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import re import sys from pathlib import Path  from validate_a1_queue_status_packet import validate as validate_queue_packet   def _load_json(path: Path) -> dict: 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[current]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[a1_wiggle_autopilot.py]] → **SOURCE_MAP_PASS**
