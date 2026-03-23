---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_codex_a1_packet_cycle::f445f1110332c40a"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_codex_a1_packet_cycle
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_codex_a1_packet_cycle::f445f1110332c40a`

## Description
codex_a1_packet_cycle.py (4797B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import subprocess from pathlib import Path   REPO = Path(__file__).resolve().parents[2] SYSTEM_V3 = REPO / "system_v3" RUNS = SYSTEM_V3 / "runs" BOOTPACK = SYSTEM_

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
