---
id: "A2_3::SOURCE_MAP_PASS::zip_dropins_dump_terms::b664cc8be25ec889"
type: "KERNEL_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "CROSS_VALIDATED"
---

# zip_dropins_dump_terms
**Node ID:** `A2_3::SOURCE_MAP_PASS::zip_dropins_dump_terms::b664cc8be25ec889`

## Description
DUMP_TERMS.txt (23416B): BEGIN DUMP_TERMS v1 BOOT_ID: BOOTPACK_THREAD_B_v3.9.13 TIMESTAMP_UTC: 2026-02-04T09:54:24Z  TERM_REGISTRY:  TERM syntax STATE TERM_PERMITTED BINDS S_PROBE_FND REQUIRED_EVIDENCE EMPTY TERM auto_accesslog STATE TERM_PERMITTED BINDS S_AUTO_MD_ANCHOR REQ

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 2 sources, 2 batches, 6 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[bootpack_thread_b_v3.9.13]]
- **DEPENDS_ON** → [[dump_terms]]

## Inward Relations
- [[QUALITY_GATE_REPORT.out.md]] → **SOURCE_MAP_PASS**
- [[TOPIC_LAYERED_EXTRACTION_DIRECTORY_LAYOUT.out.md]] → **OVERLAPS**
- [[thread_s_dump_terms]] → **EXCLUDES**
- [[dump_terms]] → **EXCLUDES**
- [[sysrepair_v2_dump_terms]] → **STRUCTURALLY_RELATED**
- [[sysrepair_v3_dump_terms]] → **STRUCTURALLY_RELATED**
- [[sysrepair_v4_dump_terms]] → **STRUCTURALLY_RELATED**
