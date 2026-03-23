---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_emit_a1_queue_surface_pydantic_sche::60367e1b2a266e6a"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_emit_a1_queue_surface_pydantic_sche
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_emit_a1_queue_surface_pydantic_sche::60367e1b2a266e6a`

## Description
emit_a1_queue_surface_pydantic_schemas.py (1523B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from a1_queue_surface_models import A1QueueCandidateRegistry, A1QueueStatusPacket   def _write_json(path: Path, payload: dict)

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
