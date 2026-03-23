---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_release_candidate_gate::8c383747df16be79"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_release_candidate_gate
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_release_candidate_gate::8c383747df16be79`

## Description
run_release_candidate_gate.py (5279B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json from pathlib import Path   BASE_REQUIRED_ARTIFACTS = [     "reports/spec_lock_report.json",     "reports/artifact_grammar_report.json",     "reports/conformance_re

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[run_codex_browser_launch_from_capture_record.py]] → **SOURCE_MAP_PASS**
- [[release_candidate_gate]] → **EXCLUDES**
- [[run_release_candidate_gate_py]] → **EXCLUDES**
