---
id: "A1_STRIPPED::CORE_DOCS_MANIFEST"
type: "REFINED_CONCEPT"
layer: "A1_STRIPPED"
authority: "CROSS_VALIDATED"
---

# CORE_DOCS_MANIFEST
**Node ID:** `A1_STRIPPED::CORE_DOCS_MANIFEST`

## Description
Core docs manifest defining the deterministic read order for core documentation. Establishes the entropy-based ingestion sequence for all core_docs/ material.

## Properties
- **dropped_jargon**: []
- **required_anchors**: ["UNVERIFIED"]

## Outward Relations
- **STRIPPED_FROM** → [[core_docs_manifest]]

## Inward Relations
- [[core_docs_manifest]] → **ROSETTA_MAP**
- [[CORE_DOCS_MANIFEST_CARTRIDGE]] → **PACKAGED_FROM**
- [[a2_state_v3_core_docs_ingest_index_v1]] → **DEPENDS_ON**
- [[a2_state_v3_index_v1]] → **DEPENDS_ON**
- [[zip_dropins_00_manifest__core_docs_order_v1]] → **DEPENDS_ON**
- [[sysrepair_v2_00_manifest__core_docs_order_v]] → **DEPENDS_ON**
- [[sysrepair_v2_core_docs_ingest_index_v1]] → **DEPENDS_ON**
- [[sysrepair_v2_index_v1]] → **DEPENDS_ON**
- [[sysrepair_v3_00_manifest__core_docs_order_v]] → **DEPENDS_ON**
- [[sysrepair_v3_core_docs_ingest_index_v1]] → **DEPENDS_ON**
- [[sysrepair_v3_index_v1]] → **DEPENDS_ON**
- [[sysrepair_v4_00_manifest__core_docs_order_v]] → **DEPENDS_ON**
- [[sysrepair_v4_core_docs_ingest_index_v1]] → **DEPENDS_ON**
- [[sysrepair_v4_index_v1]] → **DEPENDS_ON**
- [[core_docs_ingest_index_v1_json]] → **DEPENDS_ON**
