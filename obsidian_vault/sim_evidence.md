---
id: "A1_STRIPPED::SIM_EVIDENCE"
type: "REFINED_CONCEPT"
layer: "A1_STRIPPED"
authority: "CROSS_VALIDATED"
---

# SIM_EVIDENCE
**Node ID:** `A1_STRIPPED::SIM_EVIDENCE`

## Description
Canonical deterministic evidence container emitted by SIM. Bounded by BEGIN/END lines. Contains SIM_ID, CODE_HASH_SHA256, INPUT_HASH_SHA256, OUTPUT_HASH_SHA256, RUN_MANIFEST_SHA256.

## Properties
- **dropped_jargon**: []
- **required_anchors**: ["UNVERIFIED"]

## Outward Relations
- **STRIPPED_FROM** → [[sim_evidence]]

## Inward Relations
- [[sim_evidence]] → **ROSETTA_MAP**
- [[SIM_EVIDENCE_CARTRIDGE]] → **PACKAGED_FROM**
