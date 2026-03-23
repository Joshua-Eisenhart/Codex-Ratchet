---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_emit_a1_worker_send_text_companion_::fb31de762b4e5c0d"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_emit_a1_worker_send_text_companion_
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_emit_a1_worker_send_text_companion_::fb31de762b4e5c0d`

## Description
emit_a1_worker_send_text_companion_pydantic_schema.py (839B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path  from a1_worker_send_text_companion_models import A1WorkerSendTextCompanion   def main() -> int:     parser = argparse.ArgumentParser(desc

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[send_text]]

## Inward Relations
- [[create_a1_queue_candidate_registry.py]] → **SOURCE_MAP_PASS**
- [[emit_a2_controller_send_text_companion_pydantic_sc]] → **EXCLUDES**
- [[emit_a1_worker_send_text_companion_pydantic_schema]] → **EXCLUDES**
