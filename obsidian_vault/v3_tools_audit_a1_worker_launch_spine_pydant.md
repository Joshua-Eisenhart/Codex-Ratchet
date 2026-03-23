---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_a1_worker_launch_spine_pydant::384e9e1795bc7084"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_a1_worker_launch_spine_pydant
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_a1_worker_launch_spine_pydant::384e9e1795bc7084`

## Description
audit_a1_worker_launch_spine_pydantic.py (765B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path  from a1_worker_launch_spine_models import load_a1_worker_launch_spine   def main() -> int:     parser = argparse.ArgumentParser(descripti

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
