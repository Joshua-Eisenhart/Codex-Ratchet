---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_zip_job_bundle_validator::0def7da02a566279"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_zip_job_bundle_validator
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_zip_job_bundle_validator::0def7da02a566279`

## Description
zip_job_bundle_validator.py (11431B): #!/usr/bin/env python3 from __future__ import annotations  import argparse import json import re from pathlib import Path   REQUIRED_FIELDS = [     "schema",     "zip_job_id",     "zip_job_kind",     "producer_role",     "consumer_role",     "text_pr

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **EXCLUDES** → [[zip_job_bundle_validator_py]]

## Inward Relations
- [[stage_browser_observed_thread_packet.py]] → **SOURCE_MAP_PASS**
