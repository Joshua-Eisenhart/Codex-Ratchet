---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a0_structural_digest::8d0a4be7064e2e2b"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a0_structural_digest
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a0_structural_digest::8d0a4be7064e2e2b`

## Description
test_a0_structural_digest.py (7964B): import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from a0_compiler import compile_export_block from state import KernelState   def _sim_candidate(     item_id: str,     prob

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[export_block]]

## Inward Relations
- [[README.md]] → **SOURCE_MAP_PASS**
- [[control_plane_structural_digest_v1]] → **EXCLUDES**
- [[sysrepair_v2_structural_digest_v1]] → **EXCLUDES**
- [[sysrepair_v3_structural_digest_v1]] → **EXCLUDES**
- [[sysrepair_v4_structural_digest_v1]] → **EXCLUDES**
- [[structural_digest]] → **EXCLUDES**
- [[structural_digest_v1]] → **EXCLUDES**
- [[test_a0_structural_digest_py]] → **EXCLUDES**
- [[STRUCTURAL_DIGEST_DEDUP]] → **EXCLUDES**
