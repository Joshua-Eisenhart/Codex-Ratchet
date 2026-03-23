---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_operational_integrity_audit::b8726550fe0a7ca4"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a1_operational_integrity_audit
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a1_operational_integrity_audit::b8726550fe0a7ca4`

## Description
test_a1_operational_integrity_audit.py (10864B): from __future__ import annotations  import json import sys import tempfile import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[3] sys.path.insert(0, str(BASE / "tools"))  from run_a1_operational_integrity_audit import ma

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **STRUCTURALLY_RELATED** → [[v3_tools_run_a1_operational_integrity_audit]]

## Inward Relations
- [[README.md]] → **SOURCE_MAP_PASS**
- [[test_a1_operational_integrity_audit_py]] → **EXCLUDES**
- [[run_a1_operational_integrity_audit_py]] → **EXCLUDES**
