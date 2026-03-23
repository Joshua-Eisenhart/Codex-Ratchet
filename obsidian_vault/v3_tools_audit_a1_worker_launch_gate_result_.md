---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_a1_worker_launch_gate_result_::48e443628201109b"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_a1_worker_launch_gate_result_
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_a1_worker_launch_gate_result_::48e443628201109b`

## Description
audit_a1_worker_launch_gate_result_pydantic.py (831B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path  from a1_worker_launch_gate_result_models import load_a1_worker_launch_gate_result   def main() -> int:     parser = argparse.ArgumentPars

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
