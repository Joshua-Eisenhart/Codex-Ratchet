---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_prepare_codex_launch_bundle::589f4a71b6a2e0d3"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_prepare_codex_launch_bundle
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_prepare_codex_launch_bundle::589f4a71b6a2e0d3`

## Description
prepare_codex_launch_bundle.py (7683B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path  from build_a1_worker_launch_handoff import build_handoff as build_a1_handoff from build_a1_worker_send_text_from_packet import

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[send_text]]

## Inward Relations
- [[extract_parallel_codex_worker_result.py]] → **SOURCE_MAP_PASS**
- [[test_prepare_a1_launch_bundle_from_family_slice_py]] → **EXCLUDES**
- [[prepare_codex_browser_launch_bundle_from_observed_]] → **EXCLUDES**
- [[prepare_codex_launch_bundle_py]] → **EXCLUDES**
- [[prepare_a1_launch_bundle_from_family_slice_py]] → **EXCLUDES**
- [[prepare_codex_browser_launch_bundle_py]] → **EXCLUDES**
- [[v3_tools_prepare_a1_launch_bundle_from_famil]] → **STRUCTURALLY_RELATED**
- [[v3_tools_prepare_codex_browser_launch_bundle]] → **STRUCTURALLY_RELATED**
- [[v3_runtime_test_prepare_a1_launch_bundle_from_]] → **STRUCTURALLY_RELATED**
