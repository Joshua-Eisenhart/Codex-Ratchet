---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_emit_a1_worker_launch_packet_pydant::d78e0aeb8ac640cd"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_emit_a1_worker_launch_packet_pydant
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_emit_a1_worker_launch_packet_pydant::d78e0aeb8ac640cd`

## Description
emit_a1_worker_launch_packet_pydantic_schema.py (810B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path  from a1_worker_launch_packet_models import A1WorkerLaunchPacket   def main() -> int:     parser = argparse.ArgumentParser(description="Em

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
