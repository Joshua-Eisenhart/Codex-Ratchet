---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_create_a2_worker_launch_packet::7411b989b3444562"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_create_a2_worker_launch_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_create_a2_worker_launch_packet::7411b989b3444562`

## Description
create_a2_worker_launch_packet.py (3679B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   SCHEMA = "A2_WORKER_LAUNCH_PACKET_v1" THREAD_CLASS = "A2_WORKER" MODE = "A2_ONLY" ALLOWED_ROLE_TYPES = {     "A2_BRAIN_REFRES

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
