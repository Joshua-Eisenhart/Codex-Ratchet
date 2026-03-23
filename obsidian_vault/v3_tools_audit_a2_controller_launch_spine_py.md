---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_a2_controller_launch_spine_py::974ad7c938d70b73"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_a2_controller_launch_spine_py
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_a2_controller_launch_spine_py::974ad7c938d70b73`

## Description
audit_a2_controller_launch_spine_pydantic.py (781B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path  from a2_controller_launch_spine_models import load_a2_controller_launch_spine   def main() -> int:     parser = argparse.ArgumentParser(d

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
