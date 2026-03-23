---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_artifact_grammar_gate::bffab3adafc2a240"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_artifact_grammar_gate
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_artifact_grammar_gate::bffab3adafc2a240`

## Description
run_artifact_grammar_gate.py (3294B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path   def _write_json(path: Path, obj: dict) -> None:     path.parent.mkdir(parents=True, exist_ok=True)     path.write_text(json.dumps(obj, i

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[reindex_core_docs_ingest_index_v1.py]] → **SOURCE_MAP_PASS**
- [[run_artifact_grammar_gate_py]] → **EXCLUDES**
