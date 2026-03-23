---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_a1_request_to_codex_prompt::ed386fc45b1802a8"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_a1_request_to_codex_prompt
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_a1_request_to_codex_prompt::ed386fc45b1802a8`

## Description
a1_request_to_codex_prompt.py (19920B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import hashlib import json import os import textwrap import zipfile from pathlib import Path   REPO = Path(__file__).resolve().parents[2] SYSTEM_V3 = REPO / "system_v3" CORE_D

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[request]]

## Inward Relations
- [[A1_SANDBOX_ONLY_PACKET_CONTRACT_v1.md]] → **SOURCE_MAP_PASS**
