---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_thread_closeout_packets::ac9e2bf349291dcd"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_thread_closeout_packets
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_thread_closeout_packets::ac9e2bf349291dcd`

## Description
audit_thread_closeout_packets.py (3721B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from collections import Counter from pathlib import Path   def _load_packets(path: Path) -> list[dict]:     packets: list[dict] = []     if not path.exi

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
- [[audit_thread_closeout_packets_py]] → **EXCLUDES**
- [[thread_closeout_packets_000_jsonl]] → **EXCLUDES**
