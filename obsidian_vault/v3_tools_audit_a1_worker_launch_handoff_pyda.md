---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_a1_worker_launch_handoff_pyda::a9c5c744da946712"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_a1_worker_launch_handoff_pyda
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_a1_worker_launch_handoff_pyda::a9c5c744da946712`

## Description
audit_a1_worker_launch_handoff_pydantic.py (787B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path  from a1_worker_launch_handoff_models import load_a1_worker_launch_handoff   def main() -> int:     parser = argparse.ArgumentParser(descr

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
