---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_emit_a2_controller_launch_spine_pyd::5cc496d0705bdf2d"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_emit_a2_controller_launch_spine_pyd
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_emit_a2_controller_launch_spine_pyd::5cc496d0705bdf2d`

## Description
emit_a2_controller_launch_spine_pydantic_schema.py (829B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path  from a2_controller_launch_spine_models import A2ControllerLaunchSpine   def main() -> int:     parser = argparse.ArgumentParser(descripti

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]

## Inward Relations
- [[emit_a2_controller_launch_packet_pydantic_schema.py]] → **SOURCE_MAP_PASS**
- [[emit_a2_controller_launch_spine_pydantic_schema_py]] → **EXCLUDES**
- [[emit_a1_worker_launch_spine_pydantic_schema_py]] → **EXCLUDES**
