---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_auto_go_on_cycle_from_packet::5835205a85c54a17"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_auto_go_on_cycle_from_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_auto_go_on_cycle_from_packet::5835205a85c54a17`

## Description
run_auto_go_on_cycle_from_packet.py (2192B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from run_auto_go_on_cycle import main as run_cycle_main   def _load_packet(path: Path) -> dict:     if not path.exists():     

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

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
- [[v3_tools_run_auto_go_on_cycle]] → **STRUCTURALLY_RELATED**
