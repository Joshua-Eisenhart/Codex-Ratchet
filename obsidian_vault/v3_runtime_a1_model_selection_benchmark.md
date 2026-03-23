---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_a1_model_selection_benchmark::3793dc4c024580ef"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_a1_model_selection_benchmark
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_a1_model_selection_benchmark::3793dc4c024580ef`

## Description
a1_model_selection_benchmark.py (3375B): import argparse import json import time from pathlib import Path  from a1_a0_b_sim_runner import run_loop   def _write_json(path: Path, payload: dict) -> None:     path.parent.mkdir(parents=True, exist_ok=True)     path.write_text(json.dumps(payload,

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[NONCANONICAL_RUNTIME_FROZEN_IMPORT_BLOCKED_FILES.txt]] → **SOURCE_MAP_PASS**
- [[a1_model_selection_benchmark_py]] → **EXCLUDES**
