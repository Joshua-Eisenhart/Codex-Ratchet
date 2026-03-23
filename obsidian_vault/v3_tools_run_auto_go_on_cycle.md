---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_auto_go_on_cycle::8339cce5c77b25b4"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_auto_go_on_cycle
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_auto_go_on_cycle::8339cce5c77b25b4`

## Description
run_auto_go_on_cycle.py (3231B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from auto_go_on_runner import evaluate from extract_auto_go_on_thread_result import _build_packet   def main(argv: list[str]) 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[auto_go_on_runner]]
- **DEPENDS_ON** → [[packet]]
- **STRUCTURALLY_RELATED** → [[v3_tools_run_auto_go_on_cycle_from_packet]]

## Inward Relations
- [[reindex_core_docs_ingest_index_v1.py]] → **SOURCE_MAP_PASS**
- [[derived_indices_auto_go_on_cycle_packet_template_v1]] → **EXCLUDES**
- [[v3_spec_47_auto_go_on_cycle_packet__v1]] → **EXCLUDES**
- [[auto_go_on_cycle_packet]] → **EXCLUDES**
- [[create_auto_go_on_cycle_packet_py]] → **EXCLUDES**
- [[run_auto_go_on_cycle_from_packet_py]] → **EXCLUDES**
- [[run_auto_go_on_cycle_py]] → **EXCLUDES**
- [[auto_go_on_cycle_packet_template_v1_json]] → **EXCLUDES**
- [[v3_tools_create_auto_go_on_cycle_packet]] → **STRUCTURALLY_RELATED**
