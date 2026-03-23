---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_a1_model_selector::9ec269822c7f6c83"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_a1_model_selector
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_a1_model_selector::9ec269822c7f6c83`

## Description
a1_model_selector.py (2556B): import json from pathlib import Path   def _read_json(path: Path) -> dict:     return json.loads(path.read_text(encoding="utf-8"))   def find_latest_benchmark_summary(runs_root: Path) -> Path | None:     candidates = sorted(runs_root.glob("A1_MODEL_B

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[NONCANONICAL_RUNTIME_FROZEN_IMPORT_BLOCKED_FILES.txt]] → **SOURCE_MAP_PASS**
