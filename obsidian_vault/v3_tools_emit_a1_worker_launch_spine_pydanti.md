---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_emit_a1_worker_launch_spine_pydanti::5081652debe4ba7a"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_emit_a1_worker_launch_spine_pydanti
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_emit_a1_worker_launch_spine_pydanti::5081652debe4ba7a`

## Description
emit_a1_worker_launch_spine_pydantic_schema.py (813B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path  from a1_worker_launch_spine_models import A1WorkerLaunchSpine   def main() -> int:     parser = argparse.ArgumentParser(description="Emit

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
- [[emit_a2_controller_launch_spine_pydantic_schema_py]] → **EXCLUDES**
- [[emit_a1_worker_launch_spine_pydantic_schema_py]] → **EXCLUDES**
