---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_prepare_a1_launch_bundle_from_famil::c06a654c0639b381"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_prepare_a1_launch_bundle_from_famil
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_prepare_a1_launch_bundle_from_famil::c06a654c0639b381`

## Description
prepare_a1_launch_bundle_from_family_slice.py (7262B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import subprocess import sys from pathlib import Path   def _require_abs_path(path_str: str, key: str) -> Path:     path = Path(path_str)     if not path.is_absolu

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **STRUCTURALLY_RELATED** → [[v3_tools_prepare_codex_browser_launch_bundle]]
- **STRUCTURALLY_RELATED** → [[v3_tools_prepare_codex_launch_bundle]]

## Inward Relations
- [[extract_parallel_codex_worker_result.py]] → **SOURCE_MAP_PASS**
- [[test_prepare_a1_launch_bundle_from_family_slice_py]] → **EXCLUDES**
- [[prepare_codex_browser_launch_bundle_from_observed_]] → **EXCLUDES**
- [[prepare_codex_launch_bundle_py]] → **EXCLUDES**
- [[prepare_a1_launch_bundle_from_family_slice_py]] → **EXCLUDES**
- [[prepare_codex_browser_launch_bundle_py]] → **EXCLUDES**
- [[v3_runtime_test_prepare_a1_launch_bundle_from_]] → **STRUCTURALLY_RELATED**
