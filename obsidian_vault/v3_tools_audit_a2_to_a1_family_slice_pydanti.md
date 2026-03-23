---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_a2_to_a1_family_slice_pydanti::aefdc28e2945120e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_a2_to_a1_family_slice_pydanti
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_a2_to_a1_family_slice_pydanti::aefdc28e2945120e`

## Description
audit_a2_to_a1_family_slice_pydantic.py (1188B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from a2_to_a1_family_slice_models import load_family_slice   def build_result(family_slice_json: Path) -> dict:     family_sli

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
