---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_a1_consolidation_prepack_job::1816cfc815c8d959"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_a1_consolidation_prepack_job
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_a1_consolidation_prepack_job::1816cfc815c8d959`

## Description
run_a1_consolidation_prepack_job.py (30978B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import re import subprocess import sys import tempfile import time import zipfile from pathlib import Path  from a1_selector_warning_snapshot import (     build_se

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[a1_consolidation_prepack_job]]

## Inward Relations
- [[reindex_core_docs_ingest_index_v1.py]] → **SOURCE_MAP_PASS**
- [[control_plane_a1_consolidation_prepack_job__v1]] → **EXCLUDES**
- [[run_a1_consolidation_prepack_job_py]] → **EXCLUDES**
