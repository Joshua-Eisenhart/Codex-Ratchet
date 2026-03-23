---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_a1_worker_send_text_companion::5cab938d518337ca"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_a1_worker_send_text_companion
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_a1_worker_send_text_companion::5cab938d518337ca`

## Description
audit_a1_worker_send_text_companion_pydantic.py (821B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path  from a1_worker_send_text_companion_models import load_a1_worker_send_text_companion   def main() -> int:     parser = argparse.ArgumentPa

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[send_text]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
