---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_emit_a2_to_a1_family_slice_pydantic::d29c5bf4e5f0cd3f"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_emit_a2_to_a1_family_slice_pydantic
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_emit_a2_to_a1_family_slice_pydantic::d29c5bf4e5f0cd3f`

## Description
emit_a2_to_a1_family_slice_pydantic_schema.py (1140B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from a2_to_a1_family_slice_models import A2ToA1FamilySlice   def main(argv: list[str]) -> int:     parser = argparse.ArgumentP

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]

## Inward Relations
- [[emit_a2_controller_launch_packet_pydantic_schema.py]] → **SOURCE_MAP_PASS**
