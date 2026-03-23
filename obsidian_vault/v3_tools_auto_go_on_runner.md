---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_auto_go_on_runner::0f0f1189d4df8eef"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_auto_go_on_runner
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_auto_go_on_runner::0f0f1189d4df8eef`

## Description
auto_go_on_runner.py (5969B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import sys from pathlib import Path   ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER", "A2_CONTROLLER"} ALLOWED_A1_ROLES = {"A1_ROSETTA", "A1_PROPOSAL", "A1_PAC

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[audit_a1_queue_surfaces_pydantic.py]] → **SOURCE_MAP_PASS**
- [[v3_spec_45_auto_go_on_runner__v1]] → **EXCLUDES**
- [[auto_go_on_runner]] → **EXCLUDES**
- [[auto_go_on_runner_py]] → **EXCLUDES**
