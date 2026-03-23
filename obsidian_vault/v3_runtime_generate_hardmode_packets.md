---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_generate_hardmode_packets::f1553c56e3098468"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_generate_hardmode_packets
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_generate_hardmode_packets::f1553c56e3098468`

## Description
generate_hardmode_packets.py (27974B): #!/usr/bin/env python3 import argparse import hashlib import json import sys from pathlib import Path  BASE = Path(__file__).resolve().parents[1] RUNS_ROOT = BASE.parents[1] / "runs" if str(BASE) not in sys.path:     sys.path.insert(0, str(BASE))  fr

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[test_run_a1_autoratchet_cycle_audit.py]] → **SOURCE_MAP_PASS**
- [[generate_hardmode_packets_py]] → **STRUCTURALLY_RELATED**
