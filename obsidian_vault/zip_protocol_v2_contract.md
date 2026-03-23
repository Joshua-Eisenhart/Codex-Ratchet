---
id: "A1_STRIPPED::ZIP_PROTOCOL_V2_CONTRACT"
type: "REFINED_CONCEPT"
layer: "A1_STRIPPED"
authority: "CROSS_VALIDATED"
---

# ZIP_PROTOCOL_V2_CONTRACT
**Node ID:** `A1_STRIPPED::ZIP_PROTOCOL_V2_CONTRACT`

## Description
Full ZIP transport protocol: ZIP_HEADER.json (zip_protocol, zip_type, direction, source/target_layer, run_id, sequence, created_utc, compiler_version, manifest_sha256), MANIFEST.json (sorted rel_path

## Properties
- **dropped_jargon**: []
- **required_anchors**: ["UNVERIFIED"]

## Outward Relations
- **STRIPPED_FROM** → [[zip_protocol_v2_contract]]

## Inward Relations
- [[zip_protocol_v2_contract]] → **ROSETTA_MAP**
- [[ZIP_PROTOCOL_V2_CONTRACT_CARTRIDGE]] → **PACKAGED_FROM**
- [[zip_subagent_template_matrix]] → **DEPENDS_ON**
