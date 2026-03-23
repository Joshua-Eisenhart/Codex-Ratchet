---
id: "A2_3::ENGINE_PATTERN_PASS::STRUCTURAL_DIGEST_DEDUP::a697c911fe5d536f"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# STRUCTURAL_DIGEST_DEDUP
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::STRUCTURAL_DIGEST_DEDUP::a697c911fe5d536f`

## Description
Before admission, candidate export blocks are hashed (structural digest) and compared against existing survivor digests using both SHA256 exact match and Jaccard similarity. Near-duplicates are rejected to prevent ledger bloat.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **EXCLUDES** → [[control_plane_structural_digest_v1]]
- **EXCLUDES** → [[sysrepair_v2_structural_digest_v1]]
- **EXCLUDES** → [[sysrepair_v3_structural_digest_v1]]
- **EXCLUDES** → [[sysrepair_v4_structural_digest_v1]]
- **EXCLUDES** → [[v3_runtime_test_a0_structural_digest]]
- **EXCLUDES** → [[structural_digest]]
- **EXCLUDES** → [[structural_digest_v1]]
- **EXCLUDES** → [[test_a0_structural_digest_py]]

## Inward Relations
- [[a0_compiler.py]] → **ENGINE_PATTERN_PASS**
