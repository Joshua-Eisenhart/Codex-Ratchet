---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_codex_packet_only_campaign_runner::49fb82e4c8705a14"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_codex_packet_only_campaign_runner
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_codex_packet_only_campaign_runner::49fb82e4c8705a14`

## Description
codex_packet_only_campaign_runner.py (19038B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import shutil import subprocess from pathlib import Path   REPO = Path(__file__).resolve().parents[2] SYSTEM_V3 = REPO / "system_v3" RUNS_DEFAULT = SYSTEM_V3 / "ru

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
- [[v3_tools_a1_entropy_engine_campaign_runner]] → **STRUCTURALLY_RELATED**
- [[a1_entropy_engine_campaign_runner_py]] → **STRUCTURALLY_RELATED**
- [[codex_packet_only_campaign_runner_py]] → **STRUCTURALLY_RELATED**
