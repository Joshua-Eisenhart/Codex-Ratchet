---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_create_a1_worker_launch_packet::fcdb331be015bac1"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_create_a1_worker_launch_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_create_a1_worker_launch_packet::fcdb331be015bac1`

## Description
create_a1_worker_launch_packet.py (3816B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   SCHEMA = "A1_WORKER_LAUNCH_PACKET_v1" THREAD_CLASS = "A1_WORKER" MODE = "PROPOSAL_ONLY" ALLOWED_QUEUE_STATUSES = {     "READY

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
