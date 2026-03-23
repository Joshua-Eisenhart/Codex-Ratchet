---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_evidence_ingest_gate::57a910ac26c61337"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_evidence_ingest_gate
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_evidence_ingest_gate::57a910ac26c61337`

## Description
run_evidence_ingest_gate.py (7655B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path import zipfile   TEXT_SUFFIXES = {".txt", ".log", ".md", ".jsonl", ".json"}   def _write_json(path: Path, obj: dict) -> None:     path.par

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[run_codex_browser_launch_from_capture_record.py]] → **SOURCE_MAP_PASS**
