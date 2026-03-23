---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_create_auto_go_on_cycle_packet::89c0b4bdfd7a6916"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_create_auto_go_on_cycle_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_create_auto_go_on_cycle_packet::89c0b4bdfd7a6916`

## Description
create_auto_go_on_cycle_packet.py (3385B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER", "A2_CONTROLLER"}   def _require_abs(path_value: str, field: str) -> None:

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[value]]
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]
- **STRUCTURALLY_RELATED** → [[v3_tools_run_auto_go_on_cycle]]
- **STRUCTURALLY_RELATED** → [[v3_tools_run_auto_go_on_cycle_from_packet]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
- [[create_auto_go_on_cycle_packet_py]] → **STRUCTURALLY_RELATED**
- [[derived_indices_auto_go_on_cycle_packet_template_v1]] → **EXCLUDES**
- [[v3_spec_47_auto_go_on_cycle_packet__v1]] → **EXCLUDES**
- [[auto_go_on_cycle_packet]] → **EXCLUDES**
- [[run_auto_go_on_cycle_from_packet_py]] → **EXCLUDES**
- [[run_auto_go_on_cycle_py]] → **EXCLUDES**
- [[auto_go_on_cycle_packet_template_v1_json]] → **EXCLUDES**
