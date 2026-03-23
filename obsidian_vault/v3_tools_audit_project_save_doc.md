---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_audit_project_save_doc::0852f72c54457185"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_audit_project_save_doc
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_audit_project_save_doc::0852f72c54457185`

## Description
audit_project_save_doc.py (3634B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path   def _status(ok: bool) -> str:     return "PASS" if ok else "FAIL"   def main() -> int:     parser = argparse.ArgumentParser(description=

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
