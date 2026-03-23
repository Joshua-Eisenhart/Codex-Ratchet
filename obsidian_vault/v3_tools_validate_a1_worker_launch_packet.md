---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_validate_a1_worker_launch_packet::16b317afa5de8344"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_validate_a1_worker_launch_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_validate_a1_worker_launch_packet::16b317afa5de8344`

## Description
validate_a1_worker_launch_packet.py (9149B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   SCHEMA = "A1_WORKER_LAUNCH_PACKET_v1" THREAD_CLASS = "A1_WORKER" MODE = "PROPOSAL_ONLY" ALLOWED_QUEUE_STATUSES = {     "READY

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[stage_browser_observed_thread_packet.py]] → **SOURCE_MAP_PASS**
