---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_bridge_determinism_pair::78b8a1c13299a70f"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_bridge_determinism_pair
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_bridge_determinism_pair::78b8a1c13299a70f`

## Description
run_bridge_determinism_pair.py (7621B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import subprocess import hashlib import re from pathlib import Path   def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:     return subproces

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[reindex_core_docs_ingest_index_v1.py]] → **SOURCE_MAP_PASS**
- [[test_run_bridge_determinism_pair_py]] → **EXCLUDES**
- [[run_bridge_determinism_pair_py]] → **EXCLUDES**
- [[v3_runtime_test_run_bridge_determinism_pair]] → **STRUCTURALLY_RELATED**
