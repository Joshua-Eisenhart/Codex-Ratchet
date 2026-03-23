---
id: "A2_3::SOURCE_MAP_PASS::structural_digest::e2ed1d5c87f9f5f0"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# structural_digest
**Node ID:** `A2_3::SOURCE_MAP_PASS::structural_digest::e2ed1d5c87f9f5f0`

## Description
Deterministic structural fingerprint for A1 proposals to prevent fake-wiggle ID churn. Excludes IDs and self_audit, normalizes remaining schema fields.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **EXCLUDES** → [[sysrepair_v2_structural_digest_v1]]
- **EXCLUDES** → [[sysrepair_v3_structural_digest_v1]]
- **EXCLUDES** → [[sysrepair_v4_structural_digest_v1]]
- **EXCLUDES** → [[v3_runtime_test_a0_structural_digest]]
- **EXCLUDES** → [[structural_digest_v1]]
- **EXCLUDES** → [[test_a0_structural_digest_py]]

## Inward Relations
- [[STRUCTURAL_DIGEST_v1.md]] → **SOURCE_MAP_PASS**
- [[a1_strategy_schema_and_repair]] → **DEPENDS_ON**
- [[promotion_binding_and_evidence_digests]] → **DEPENDS_ON**
- [[control_plane_structural_digest_v1]] → **DEPENDS_ON**
- [[STRUCTURAL_DIGEST_DEDUP]] → **EXCLUDES**
- [[events_000_jsonl]] → **DEPENDS_ON**
- [[a0_compile_0001_json]] → **DEPENDS_ON**
