---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_snapshot::d6b351731dd52960"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_snapshot
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_snapshot::d6b351731dd52960`

## Description
snapshot.py (2441B): from state import KernelState   def build_snapshot_v2(     state: KernelState,     boot_id: str = "BOOTPACK_THREAD_B_v3.9.13",     timestamp_utc: str = "",     lexicographic: bool = True, ) -> str:     lines: list[str] = []     lines.append("BEGIN TH

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[bootpack_thread_b_v3.9.13]]

## Inward Relations
- [[NONCANONICAL_RUNTIME_FROZEN_IMPORT_BLOCKED_FILES.txt]] → **SOURCE_MAP_PASS**
