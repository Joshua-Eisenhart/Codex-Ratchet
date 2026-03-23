---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_a1_sandbox_only_runner::f1d1fce50d33acc0"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_a1_sandbox_only_runner
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_a1_sandbox_only_runner::f1d1fce50d33acc0`

## Description
a1_sandbox_only_runner.py (16114B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import time from dataclasses import dataclass from pathlib import Path  REPO = Path(__file__).resolve().parents[2] CORE_DOCS = REPO / "core_docs" SY

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[sandbox]]

## Inward Relations
- [[A1_SANDBOX_ONLY_PACKET_CONTRACT_v1.md]] → **SOURCE_MAP_PASS**
- [[a1_sandbox_only_runner_py]] → **EXCLUDES**
