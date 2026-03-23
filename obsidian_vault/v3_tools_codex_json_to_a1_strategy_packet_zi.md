---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_codex_json_to_a1_strategy_packet_zi::3d57b631d30d083e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_codex_json_to_a1_strategy_packet_zi
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_codex_json_to_a1_strategy_packet_zi::3d57b631d30d083e`

## Description
codex_json_to_a1_strategy_packet_zip.py (4402B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys import zipfile from pathlib import Path   REPO = Path(__file__).resolve().parents[2] BOOTPACK = REPO / "system_v3" / "runtime" / "bootpack_b_kernel_v1" 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
